from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.orm import Conversation, Message, User, TokenUsage, ConfluenceConfig
from app.config import settings
from app.services.azure_openai_service import AzureOpenAIService
from app.services.confluence_service import ConfluenceService
from app.services.tool_executor import ToolExecutor
from app.services.tools import CONFLUENCE_TOOLS, SYSTEM_PROMPT
from app.services.document_parser_service import document_parser
from app.utils.logger import setup_logger
from typing import List, Dict, AsyncGenerator, Any, Callable, Optional
from pathlib import Path
import asyncio
import json
import base64
import mimetypes

# Maximum messages to keep in context
MAX_CONTEXT_MESSAGES = 20
UPLOAD_DIR = Path("/app/uploads")

logger = setup_logger("chat_service")

class ChatService:
    def __init__(self, db: Session, user_id: int = None):
        self.db = db
        self.user_id = user_id
        self.openai_service = AzureOpenAIService()
        self._gemini_service = None  # Lazy init
        self.confluence_service = self._get_user_confluence_service(user_id)
        self.tool_executor = ToolExecutor(self.confluence_service)

    @property
    def gemini_service(self):
        if self._gemini_service is None:
            if not settings.VERTEX_API_KEY:
                raise ValueError("Vertex AI API Key 未配置，无法使用 Gemini 模型")
            from app.services.gemini_service import GeminiService
            self._gemini_service = GeminiService()
        return self._gemini_service

    def _get_user_confluence_service(self, user_id: int) -> Optional[ConfluenceService]:
        """Get Confluence service with user's credentials"""
        if not user_id:
            logger.warning("No user_id provided for Confluence service")
            return None

        config = self.db.query(ConfluenceConfig).filter(
            ConfluenceConfig.user_id == user_id,
            ConfluenceConfig.is_active == True
        ).first()

        if not config:
            logger.warning(f"No Confluence config found for user {user_id}")
            return None

        try:
            api_token = ConfluenceService.decrypt_token(config.api_token_encrypted)
            logger.info(f"Creating Confluence service for user {user_id}, email={config.email}, base_url={config.base_url}, token_len={len(api_token)}")
            service = ConfluenceService(
                base_url=config.base_url,
                username=config.email,
                api_key=api_token
            )
            logger.info(f"Service created: username={service.username}, api_key_len={len(service.api_key)}, auth=({service.auth[0]}, len={len(service.auth[1])})")
            return service
        except Exception as e:
            logger.error(f"Failed to create Confluence service for user {user_id}: {e}")
            return None

    def create_conversation(self, user_id: int, title: str = None) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(user_id=user_id, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: int, user_id: int) -> Conversation:
        """Get conversation by ID"""
        return self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()

    def get_user_conversations(self, user_id: int, limit: int = 50) -> List[Conversation]:
        """Get user's conversations"""
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(
            Conversation.updated_at.desc(),
            Conversation.id.desc()  # Secondary sort key for deterministic ordering
        ).limit(limit).all()

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        image_url: str = None,
        image_urls: List[str] = None
    ) -> Message:
        """Add message to conversation"""
        # Support both single image_url and multiple image_urls
        file_urls = image_urls if image_urls else ([image_url] if image_url else [])
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            image_url=image_url or (file_urls[0] if file_urls else None),
            file_urls=file_urls
        )
        self.db.add(message)

        # Update conversation's updated_at for proper sorting
        conversation = self.db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        if conversation:
            conversation.updated_at = func.now()

        self.db.commit()
        self.db.refresh(message)
        return message

    def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        """Get all messages in a conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

    def _get_image_data_url(self, image_url: str) -> Optional[str]:
        """Convert relative image URL to base64 data URL for OpenAI Vision API"""
        if not image_url:
            return None

        # If already a data URL or full URL, return as-is
        if image_url.startswith('data:') or image_url.startswith('http'):
            return image_url

        # Handle relative upload URL
        if image_url.startswith('/uploads/'):
            relative_path = image_url[9:]  # Remove "/uploads/"
            file_path = UPLOAD_DIR / relative_path
            if file_path.exists():
                try:
                    content_type, _ = mimetypes.guess_type(str(file_path))
                    if not content_type:
                        content_type = 'image/png'
                    with open(file_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                    return f"data:{content_type};base64,{image_data}"
                except Exception as e:
                    logger.error(f"Failed to read image {file_path}: {e}")
                    return None
        return None

    def _get_document_content(self, file_url: str) -> Optional[str]:
        """
        Parse document file and return text content

        Args:
            file_url: Relative URL like /uploads/xxx.pdf

        Returns:
            Extracted text content or None
        """
        if not file_url:
            return None

        # Handle relative upload URL
        if file_url.startswith('/uploads/'):
            relative_path = file_url[9:]  # Remove "/uploads/"
            file_path = UPLOAD_DIR / relative_path
            if file_path.exists() and document_parser.is_document(str(file_path)):
                return document_parser.parse_file(str(file_path))

        return None

    def build_message_history(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Build message history for OpenAI API with document and image support"""
        history = []
        for msg in messages:
            # Get all file URLs from file_urls or fallback to single image_url
            all_file_urls = msg.file_urls if msg.file_urls else ([msg.image_url] if msg.image_url else [])
            all_file_urls = [url for url in all_file_urls if url]  # Filter out None/empty

            # Separate images and documents
            image_urls = []
            document_contents = []

            for url in all_file_urls:
                # Check if it's a document
                doc_content = self._get_document_content(url)
                if doc_content:
                    # Extract filename from URL
                    filename = url.split('/')[-1] if '/' in url else url
                    document_contents.append(f"[文件: {filename}]\n{doc_content}")
                else:
                    # Treat as image
                    image_urls.append(url)

            # Build text content with document attachments
            text_content = msg.content or ""
            if document_contents:
                attachment_text = "\n\n附件内容：\n" + "\n\n---\n\n".join(document_contents)
                text_content = text_content + attachment_text if text_content else attachment_text
                logger.info(f"Attached {len(document_contents)} document(s) to message")

            message_dict = {"role": msg.role, "content": text_content}

            # Build multimodal content with images
            if image_urls:
                # Add image path info to text content so AI knows the file_url for upload_attachment_to_confluence
                image_path_info = "\n\n[上传的图片文件路径: " + ", ".join(image_urls) + "]"
                enriched_text = (text_content + image_path_info) if text_content else ("请看这些图片" + image_path_info)
                content_parts = [{"type": "text", "text": enriched_text}]
                for url in image_urls:
                    data_url = self._get_image_data_url(url)
                    if data_url:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": data_url, "detail": "high"}
                        })
                if len(content_parts) > 1:  # Has at least one image
                    message_dict["content"] = content_parts

            history.append(message_dict)
        return history

    def build_message_history_with_limit(self, messages: List[Message], max_messages: int = MAX_CONTEXT_MESSAGES) -> List[Dict[str, str]]:
        """Build message history with context limit"""
        recent = messages[-max_messages:] if len(messages) > max_messages else messages
        return self.build_message_history(recent)

    def record_token_usage(self, user_id: int, conversation_id: int, prompt_tokens: int, completion_tokens: int, model: str = "gpt-5.1"):
        """Record token usage to database"""
        try:
            usage = TokenUsage(
                user_id=user_id,
                conversation_id=conversation_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                model=model
            )
            self.db.add(usage)
            self.db.commit()
            logger.info(
                f"Token usage | user_id={user_id} | conv_id={conversation_id} | "
                f"prompt={prompt_tokens} | completion={completion_tokens} | "
                f"total={prompt_tokens + completion_tokens} | model={model}"
            )
        except Exception as e:
            logger.error(f"Failed to record token usage: {e}")
            self.db.rollback()

    async def generate_title(self, user_message: str) -> str:
        """Generate a short title from the first user message"""
        prompt = [
            {"role": "system", "content": "根据用户的问题生成一个简短的对话标题（不超过20个字符）。只返回标题，不要任何解释或标点符号。"},
            {"role": "user", "content": user_message}
        ]
        try:
            title = await self.openai_service.chat_completion(prompt, temperature=0.3, max_tokens=50)
            # Clean up and truncate
            title = title.strip().strip('"\'')[:30]
            return title if title else user_message[:20]
        except Exception:
            # Fallback to truncated user message
            return user_message[:20] + ("..." if len(user_message) > 20 else "")

    def update_conversation_title(self, conversation_id: int, title: str):
        """Update conversation title"""
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.title = title
            self.db.commit()

    async def chat_stream(
        self,
        conversation_id: int,
        user_message: str,
        image_url: str = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat response"""
        # Add user message
        self.add_message(conversation_id, "user", user_message, image_url)

        # Get conversation history
        messages = self.get_conversation_messages(conversation_id)
        message_history = self.build_message_history(messages)

        # Stream AI response
        full_response = ""
        async for chunk in self.openai_service.chat_completion_stream(message_history):
            full_response += chunk
            yield chunk

        # Save AI response
        self.add_message(conversation_id, "assistant", full_response)

    async def chat_stream_with_tools(
        self,
        conversation_id: int,
        user_message: str,
        user_id: int = None,
        image_urls: List[str] = None,
        file_urls: List[str] = None,
        model: str = "gpt-5.1",
        on_tool_call: Callable[[str, str], None] = None,
        on_tool_result: Callable[[str, Dict], None] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response with tool calling support"""
        # Lazy reload: if confluence_service was not available at init time,
        # try loading it now (user may have saved config after opening chat)
        if self.confluence_service is None and self.user_id:
            self.confluence_service = self._get_user_confluence_service(self.user_id)
            if self.confluence_service:
                self.tool_executor = ToolExecutor(self.confluence_service)
                logger.info(f"Lazy-loaded Confluence service for user {self.user_id}")

        # Merge image_urls and file_urls for storage
        all_urls = []
        if image_urls:
            all_urls.extend(image_urls)
        if file_urls:
            all_urls.extend(file_urls)

        # Add user message with all file URLs
        self.add_message(conversation_id, "user", user_message, image_urls=all_urls if all_urls else None)

        # Get conversation history with limit and add system prompt
        messages = self.get_conversation_messages(conversation_id)
        message_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        message_history.extend(self.build_message_history_with_limit(messages))

        max_iterations = 5
        iteration = 0
        last_tool_name = None
        same_tool_count = 0
        total_prompt_tokens = 0
        total_completion_tokens = 0
        has_tool_executed = False

        while iteration < max_iterations:
            iteration += 1
            full_content = ""
            content_buffer = []
            tool_calls = []
            raw_model_content = None  # For Gemini thought_signature preservation

            # Stream response - route to appropriate service
            if model == "gemini-3-pro":
                stream = self.gemini_service.chat_completion_with_tools_stream(
                    message_history, tools=CONFLUENCE_TOOLS
                )
            else:
                deployment = settings.AZURE_CHAT_DEPLOYMENT_52 if model == "gpt-5.2" else None
                stream = self.openai_service.chat_completion_with_tools_stream(
                    message_history, tools=CONFLUENCE_TOOLS, deployment=deployment
                )
            async for chunk in stream:
                if chunk["type"] == "thinking":
                    yield {"type": "thinking", "content": chunk["content"]}
                elif chunk["type"] == "content":
                    full_content += chunk["content"]
                    content_buffer.append(chunk["content"])
                    # Buffer content - don't yield yet; decide after stream ends
                elif chunk["type"] == "tool_calls":
                    tool_calls = chunk["tool_calls"]
                    raw_model_content = chunk.get("_raw_model_content")
                elif chunk["type"] == "usage":
                    total_prompt_tokens += chunk.get("prompt_tokens", 0)
                    total_completion_tokens += chunk.get("completion_tokens", 0)
                elif chunk["type"] == "finish":
                    pass

            # Route buffered content:
            # - If tool_calls follow → content is intermediate reasoning, redirect to thinking
            # - If no tool_calls → content is the final answer, flush as content
            if tool_calls and full_content.strip():
                yield {"type": "thinking", "content": full_content}
            else:
                for c in content_buffer:
                    yield {"type": "content", "content": c}

            # If no tool calls, we're done
            if not tool_calls:
                if full_content:
                    self.add_message(conversation_id, "assistant", full_content)
                elif has_tool_executed:
                    # Tool was executed but AI returned empty - force a response
                    message_history.append({
                        "role": "system",
                        "content": "请根据上述工具执行结果，向用户提供简洁的总结或回答。"
                    })
                    # Get a non-streaming response
                    try:
                        if model == "gemini-3-pro":
                            forced_response = await self.gemini_service.chat_completion(message_history, max_tokens=1000)
                        else:
                            deployment = settings.AZURE_CHAT_DEPLOYMENT_52 if model == "gpt-5.2" else None
                            forced_response = await self.openai_service.chat_completion(message_history, max_tokens=1000, deployment=deployment)
                        if forced_response and forced_response.strip():
                            yield {"type": "content", "content": forced_response}
                            self.add_message(conversation_id, "assistant", forced_response)
                        else:
                            default_msg = "操作已完成。请查看上方的工具执行结果。"
                            yield {"type": "content", "content": default_msg}
                            self.add_message(conversation_id, "assistant", default_msg)
                    except Exception as e:
                        logger.error(f"Failed to generate forced response: {e}")
                        default_msg = "操作已完成。请查看上方的工具执行结果。"
                        yield {"type": "content", "content": default_msg}
                        self.add_message(conversation_id, "assistant", default_msg)
                break

            # Add assistant message with tool calls to history
            assistant_msg = {
                "role": "assistant",
                "content": full_content or None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]}
                    }
                    for tc in tool_calls
                ]
            }
            # Preserve raw Gemini Content for thought_signature (thinking model)
            if raw_model_content is not None:
                assistant_msg["_gemini_content"] = raw_model_content
            message_history.append(assistant_msg)

            # Execute tool calls
            for tc in tool_calls:
                tool_name = tc["name"]

                try:
                    arguments = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    arguments = {}

                # Create a signature for this tool call (name + key args)
                call_signature = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"

                # Prevent repeated IDENTICAL tool calls (same tool + same arguments)
                if call_signature == last_tool_name:
                    same_tool_count += 1
                    if same_tool_count >= 2:
                        yield {"type": "content", "content": "\n\n检测到重复操作（相同参数），已停止。"}
                        yield {"type": "done"}
                        return
                else:
                    same_tool_count = 0
                last_tool_name = call_signature

                # Notify tool call start
                logger.info(f"Tool call: {tool_name}, args: {arguments}")
                yield {"type": "tool_call", "tool_name": tool_name, "status": "executing"}
                if on_tool_call:
                    on_tool_call(tool_name, "executing")

                # Execute tool
                result = await self.tool_executor.execute(tool_name, arguments)

                # Extract downloaded images before JSON serialization (pop internal field)
                downloaded_images = None
                if isinstance(result, dict):
                    downloaded_images = result.pop("_downloaded_images", None)

                if result.get('success'):
                    logger.info(f"Tool result: {tool_name}, success: True")
                else:
                    logger.error(f"Tool result: {tool_name}, success: False, error: {result.get('error', 'Unknown error')}")
                has_tool_executed = True

                # Notify tool result
                yield {"type": "tool_result", "tool_name": tool_name, "result": result}
                if on_tool_result:
                    on_tool_result(tool_name, result)

                # Add tool result to history
                message_history.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, ensure_ascii=False)
                })

                # Inject downloaded images as a synthetic user message for AI vision
                if downloaded_images:
                    filenames = ", ".join(img["filename"] for img in downloaded_images)
                    content_parts = [
                        {
                            "type": "text",
                            "text": f"[系统：以下是从 Confluence 页面提取的 {len(downloaded_images)} 张图片（{filenames}），请结合图片内容回答用户问题]"
                        }
                    ]
                    for img in downloaded_images:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": img["data_url"], "detail": "auto"}
                        })
                    message_history.append({
                        "role": "user",
                        "content": content_parts
                    })
                    logger.info(f"Injected {len(downloaded_images)} images into message history for AI vision")

        # Record token usage if user_id provided
        if user_id and (total_prompt_tokens > 0 or total_completion_tokens > 0):
            self.record_token_usage(user_id, conversation_id, total_prompt_tokens, total_completion_tokens, model=model)

        yield {"type": "done"}
