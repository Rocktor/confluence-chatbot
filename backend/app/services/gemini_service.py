from google import genai
from google.genai import types
from app.config import settings
from app.utils.logger import setup_logger
from typing import List, Dict, AsyncGenerator, Any
import json
import uuid
import base64

logger = setup_logger("gemini_service")


class GeminiService:
    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            api_key=settings.VERTEX_API_KEY,
        )
        self.model = "gemini-3-pro-preview"
        self.max_output_tokens = 65536

    def _convert_openai_tools_to_gemini(self, openai_tools: List[Dict]) -> List[types.Tool]:
        """Convert OpenAI tool definitions to Gemini FunctionDeclarations"""
        if not openai_tools:
            return None

        declarations = []
        for tool in openai_tools:
            if tool.get("type") != "function":
                continue
            func = tool["function"]
            decl = types.FunctionDeclaration(
                name=func["name"],
                description=func.get("description", ""),
                parameters_json_schema=func.get("parameters") or None,
            )
            declarations.append(decl)

        return [types.Tool(function_declarations=declarations)] if declarations else None

    def _find_func_name_for_tool_call_id(self, messages: List[Dict], tool_call_id: str) -> str:
        """Find function name from assistant message by tool_call_id"""
        for msg in messages:
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls", []):
                    if tc.get("id") == tool_call_id:
                        return tc.get("function", {}).get("name", "")
        return ""

    def _convert_messages_to_gemini_contents(self, messages: List[Dict]):
        """Convert OpenAI message format to Gemini Contents + system_instruction.

        Supports '_gemini_content' key on assistant messages to preserve raw
        Gemini Content (including thought_signature for thinking models).
        """
        system_instruction = None
        items = []  # list of (gemini_role, [parts])

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "system":
                if isinstance(content, str):
                    system_instruction = content
                continue

            if role == "user":
                parts = []
                if isinstance(content, str):
                    if content:
                        parts.append(types.Part.from_text(text=content))
                elif isinstance(content, list):
                    # Multimodal content
                    for item in content:
                        if item.get("type") == "text":
                            parts.append(types.Part.from_text(text=item["text"]))
                        elif item.get("type") == "image_url":
                            url = item["image_url"]["url"]
                            if url.startswith("data:"):
                                header, data = url.split(",", 1)
                                mime_type = header.split(":")[1].split(";")[0]
                                parts.append(types.Part.from_bytes(
                                    data=base64.b64decode(data),
                                    mime_type=mime_type,
                                ))
                if parts:
                    items.append(("user", parts))

            elif role == "assistant":
                # Use raw Gemini Content if available (preserves thought_signature)
                raw_content = msg.get("_gemini_content")
                if raw_content and isinstance(raw_content, types.Content):
                    items.append(("model", list(raw_content.parts)))
                else:
                    parts = []
                    if content:
                        parts.append(types.Part.from_text(text=content))
                    for tc in msg.get("tool_calls", []):
                        func = tc.get("function", {})
                        try:
                            args = json.loads(func.get("arguments", "{}"))
                        except json.JSONDecodeError:
                            args = {}
                        parts.append(types.Part.from_function_call(
                            name=func.get("name", ""),
                            args=args,
                        ))
                    if parts:
                        items.append(("model", parts))

            elif role == "tool":
                tool_call_id = msg.get("tool_call_id", "")
                func_name = self._find_func_name_for_tool_call_id(messages, tool_call_id)
                try:
                    response_data = json.loads(content) if isinstance(content, str) else content or {}
                except json.JSONDecodeError:
                    response_data = {"result": content}

                part = types.Part.from_function_response(
                    name=func_name,
                    response=response_data,
                )
                items.append(("user", [part]))

        # Merge consecutive same-role items into single Content
        contents = []
        for gemini_role, parts in items:
            if contents and contents[-1].role == gemini_role:
                merged = list(contents[-1].parts) + parts
                contents[-1] = types.Content(role=gemini_role, parts=merged)
            else:
                contents.append(types.Content(role=gemini_role, parts=parts))

        return system_instruction, contents

    async def chat_completion_with_tools_stream(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming chat completion with tool calling support.
        Yields dicts matching AzureOpenAIService format:
        - {"type": "content", "content": str}
        - {"type": "tool_calls", "tool_calls": [...], "_raw_model_content": Content}
        - {"type": "usage", "prompt_tokens": int, "completion_tokens": int}
        - {"type": "finish", "finish_reason": str}
        """
        system_instruction, contents = self._convert_messages_to_gemini_contents(messages)
        gemini_tools = self._convert_openai_tools_to_gemini(tools)

        config_kwargs = {
            "temperature": temperature,
            "max_output_tokens": self.max_output_tokens,
            "thinking_config": types.ThinkingConfig(include_thoughts=True),
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction
        if gemini_tools:
            config_kwargs["tools"] = gemini_tools
            config_kwargs["automatic_function_calling"] = types.AutomaticFunctionCallingConfig(disable=True)

        config = types.GenerateContentConfig(**config_kwargs)

        function_calls = []
        all_parts = []  # Accumulate all parts to preserve thought_signatures
        prompt_tokens = 0
        completion_tokens = 0

        try:
            async for chunk in await self.client.aio.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=config,
            ):
                # Iterate parts to detect thinking vs content vs function calls
                if hasattr(chunk, 'candidates') and chunk.candidates:
                    for candidate in chunk.candidates:
                        if not (hasattr(candidate, 'content') and candidate.content and candidate.content.parts):
                            continue
                        for part in candidate.content.parts:
                            # Collect all raw parts (preserves thought_signature)
                            all_parts.append(part)
                            if getattr(part, 'thought', False) and part.text:
                                # Thinking part from the model
                                yield {"type": "thinking", "content": part.text}
                            elif part.text and not getattr(part, 'thought', False):
                                # Normal text content
                                yield {"type": "content", "content": part.text}
                            elif hasattr(part, 'function_call') and part.function_call:
                                fc = part.function_call
                                function_calls.append({
                                    "id": f"call_{uuid.uuid4().hex[:24]}",
                                    "name": fc.name,
                                    "arguments": json.dumps(fc.args or {}, ensure_ascii=False),
                                })

                # Handle usage metadata (typically on last chunk)
                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                    um = chunk.usage_metadata
                    if hasattr(um, 'prompt_token_count') and um.prompt_token_count:
                        prompt_tokens = um.prompt_token_count
                    if hasattr(um, 'candidates_token_count') and um.candidates_token_count:
                        completion_tokens = um.candidates_token_count

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}", exc_info=True)
            raise

        # Yield accumulated function calls with complete Content (includes thought_signatures)
        if function_calls:
            # Build complete Content from all accumulated parts
            raw_model_content = types.Content(role="model", parts=all_parts) if all_parts else None
            yield {
                "type": "tool_calls",
                "tool_calls": function_calls,
                "_raw_model_content": raw_model_content,
            }

        # Yield usage
        if prompt_tokens > 0 or completion_tokens > 0:
            yield {"type": "usage", "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens}

        # Yield finish
        finish_reason = "tool_calls" if function_calls else "stop"
        yield {"type": "finish", "finish_reason": finish_reason}

    async def chat_completion(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = None,
    ) -> str:
        """Non-streaming chat completion (used for forced_response)"""
        system_instruction, contents = self._convert_messages_to_gemini_contents(messages)

        config_kwargs = {
            "temperature": temperature,
            "max_output_tokens": max_tokens or self.max_output_tokens,
        }
        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        config = types.GenerateContentConfig(**config_kwargs)

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        return response.text or ""
