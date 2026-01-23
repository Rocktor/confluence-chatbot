from sqlalchemy.orm import Session
from app.models.orm import Conversation, Message, User, TokenUsage, ConfluenceConfig
from app.services.azure_openai_service import AzureOpenAIService
from app.services.confluence_service import ConfluenceService
from app.services.tool_executor import ToolExecutor
from app.services.tools import CONFLUENCE_TOOLS, SYSTEM_PROMPT
from app.utils.logger import setup_logger
from typing import List, Dict, AsyncGenerator, Any, Callable, Optional
import asyncio
import json

# Maximum messages to keep in context
MAX_CONTEXT_MESSAGES = 20

logger = setup_logger("chat_service")

class ChatService:
    def __init__(self, db: Session, user_id: int = None):
        self.db = db
        self.openai_service = AzureOpenAIService()
        self.confluence_service = self._get_user_confluence_service(user_id)
        self.tool_executor = ToolExecutor(self.confluence_service)

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
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        image_url: str = None
    ) -> Message:
        """Add message to conversation"""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            image_url=image_url
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_conversation_messages(self, conversation_id: int) -> List[Message]:
        """Get all messages in a conversation"""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc()).all()

    def build_message_history(self, messages: List[Message]) -> List[Dict[str, str]]:
        """Build message history for OpenAI API"""
        history = []
        for msg in messages:
            message_dict = {"role": msg.role, "content": msg.content}
            if msg.image_url:
                message_dict["content"] = [
                    {"type": "text", "text": msg.content},
                    {"type": "image_url", "image_url": {"url": msg.image_url}}
                ]
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
        image_url: str = None,
        on_tool_call: Callable[[str, str], None] = None,
        on_tool_result: Callable[[str, Dict], None] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response with tool calling support"""
        # Add user message
        self.add_message(conversation_id, "user", user_message, image_url)

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
            tool_calls = []

            # Stream response
            async for chunk in self.openai_service.chat_completion_with_tools_stream(
                message_history, tools=CONFLUENCE_TOOLS
            ):
                if chunk["type"] == "content":
                    full_content += chunk["content"]
                    yield {"type": "content", "content": chunk["content"]}
                elif chunk["type"] == "tool_calls":
                    tool_calls = chunk["tool_calls"]
                elif chunk["type"] == "usage":
                    total_prompt_tokens += chunk.get("prompt_tokens", 0)
                    total_completion_tokens += chunk.get("completion_tokens", 0)
                elif chunk["type"] == "finish":
                    pass

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
                        forced_response = await self.openai_service.chat_completion(message_history, max_tokens=1000)
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
            message_history.append({
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
            })

            # Execute tool calls
            for tc in tool_calls:
                tool_name = tc["name"]

                # Prevent repeated same tool calls
                if tool_name == last_tool_name:
                    same_tool_count += 1
                    if same_tool_count >= 2:
                        yield {"type": "content", "content": "\n\n检测到重复操作，已停止。"}
                        yield {"type": "done"}
                        return
                else:
                    same_tool_count = 0
                last_tool_name = tool_name

                try:
                    arguments = json.loads(tc["arguments"])
                except json.JSONDecodeError:
                    arguments = {}

                # Notify tool call start
                logger.info(f"Tool call: {tool_name}, args: {arguments}")
                yield {"type": "tool_call", "tool_name": tool_name, "status": "executing"}
                if on_tool_call:
                    on_tool_call(tool_name, "executing")

                # Execute tool
                result = await self.tool_executor.execute(tool_name, arguments)
                logger.info(f"Tool result: {tool_name}, success: {result.get('success', False)}")
                has_tool_executed = True

                # Notify tool result
                yield {"type": "tool_result", "tool_name": tool_name, "result": result}
                if on_tool_result:
                    on_tool_result(tool_name, result)

                # Add tool result to history
                # Handle multimodal results (images)
                if result.get("_multimodal") and result.get("images"):
                    # Build multimodal content for GPT Vision
                    content_parts = [
                        {"type": "text", "text": f"以下是页面「{result.get('title', '')}」中的 {result.get('image_count', 0)} 张图片，请仔细观察并描述每张图片的内容："}
                    ]
                    for img in result["images"]:
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": img["data_url"],
                                "detail": "high"
                            }
                        })
                    message_history.append({
                        "role": "user",
                        "content": content_parts
                    })
                    # Also add a tool response to satisfy the API
                    message_history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps({
                            "success": True,
                            "message": result.get("message", "图片已加载"),
                            "image_count": result.get("image_count", 0),
                            "filenames": [img["filename"] for img in result["images"]]
                        }, ensure_ascii=False)
                    })
                else:
                    # Regular text result
                    message_history.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result, ensure_ascii=False)
                    })

        # Record token usage if user_id provided
        if user_id and (total_prompt_tokens > 0 or total_completion_tokens > 0):
            self.record_token_usage(user_id, conversation_id, total_prompt_tokens, total_completion_tokens)

        yield {"type": "done"}
