from openai import AsyncAzureOpenAI
from app.config import settings
from typing import List, Dict, AsyncGenerator, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

class AzureOpenAIService:
    def __init__(self):
        self.client = AsyncAzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.chat_deployment = settings.AZURE_CHAT_DEPLOYMENT
        self.embedding_deployment = settings.AZURE_EMBEDDING_DEPLOYMENT
        # GPT-5.1: max output 128K, set to 64K for balance
        self.max_completion_tokens = 65536

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion responses"""
        response = await self.client.chat.completions.create(
            model=self.chat_deployment,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens or self.max_completion_tokens,
            stream=True
        )

        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> str:
        """Get chat completion response"""
        response = await self.client.chat.completions.create(
            model=self.chat_deployment,
            messages=messages,
            temperature=temperature,
            max_completion_tokens=max_tokens or self.max_completion_tokens
        )
        return response.choices[0].message.content

    async def create_embedding(self, text: str) -> List[float]:
        """Create text embedding"""
        response = await self.client.embeddings.create(
            model=self.embedding_deployment,
            input=text
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    async def chat_completion_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Chat completion with tool calling support (non-streaming)"""
        kwargs = {
            "model": self.chat_deployment,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": self.max_completion_tokens
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        return {
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments
                }
                for tc in (message.tool_calls or [])
            ],
            "finish_reason": response.choices[0].finish_reason
        }

    async def chat_completion_with_tools_stream(
        self,
        messages: List[Dict],
        tools: List[Dict] = None,
        tool_choice: str = "auto",
        temperature: float = 0.7
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming chat completion with tool calling support"""
        kwargs = {
            "model": self.chat_deployment,
            "messages": messages,
            "temperature": temperature,
            "max_completion_tokens": self.max_completion_tokens,
            "stream": True,
            "stream_options": {"include_usage": True}
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = await self.client.chat.completions.create(**kwargs)

        tool_calls_buffer = {}
        async for chunk in response:
            # Handle usage info (comes at the end with stream_options)
            if hasattr(chunk, 'usage') and chunk.usage:
                yield {
                    "type": "usage",
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens
                }
                continue

            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta
            finish_reason = chunk.choices[0].finish_reason

            # Handle content
            if delta.content:
                yield {"type": "content", "content": delta.content}

            # Handle tool calls
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                    if tc.id:
                        tool_calls_buffer[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tc.function.arguments

            # Handle finish
            if finish_reason:
                if finish_reason == "tool_calls" and tool_calls_buffer:
                    yield {
                        "type": "tool_calls",
                        "tool_calls": list(tool_calls_buffer.values())
                    }
                yield {"type": "finish", "finish_reason": finish_reason}
