"""Grok AI provider (text-only, requires external TTS/STT)."""

from typing import Optional, AsyncIterator
import httpx
import json

from .ai_provider import (
    AIProvider,
    AIMessage,
    AIResponse,
    MessageRole,
    ToolDefinition,
)


class GrokProvider(AIProvider):
    """Provider using Grok API (text-based, no native audio)."""

    def __init__(self, api_key: str, model: str = "grok-2"):
        self.api_key = api_key
        self.model = model
        self.client = None

    async def initialize(self) -> None:
        """Initialize HTTP client for Grok API."""
        self.client = httpx.AsyncClient()

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    async def send_message(
        self,
        message: AIMessage,
        conversation_history: list[AIMessage],
        system_prompt: str,
        tools: Optional[list[ToolDefinition]] = None,
    ) -> AsyncIterator[AIResponse]:
        """
        Send message to Grok API and stream responses.

        Grok is text-only, so audio input/output requires external TTS/STT.
        """
        if not self.client:
            raise RuntimeError("Provider not initialized")

        # Build message history
        messages = []

        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add conversation history (text only)
        for msg in conversation_history:
            if msg.content:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        # Add current message (text only)
        if message.content:
            messages.append({
                "role": "user",
                "content": message.content,
            })

        # Convert tools to Grok format if supported
        tools_config = None
        if tools:
            tools_config = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]

        # Call Grok API with streaming
        request_data = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        if tools_config:
            request_data["tools"] = tools_config

        async with self.client.stream(
            "POST",
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=request_data,
        ) as response:
            if response.status_code != 200:
                text = await response.atext()
                raise RuntimeError(f"Grok API error: {text}")

            async for line in response.aiter_lines():
                if not line or line.startswith("[DONE]"):
                    continue

                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])
                        yield self._process_chunk(chunk)
                    except json.JSONDecodeError:
                        continue

    def _process_chunk(self, chunk: dict) -> AIResponse:
        """Convert Grok API chunk to AIResponse."""
        choices = chunk.get("choices", [])
        if not choices:
            return AIResponse(has_more=True)

        choice = choices[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")

        # Extract text content
        text = delta.get("content", "")

        # Extract tool calls if present
        tool_calls = None
        if "tool_calls" in delta:
            tool_calls = []
            for tool_call in delta["tool_calls"]:
                tool_calls.append({
                    "name": tool_call.get("function", {}).get("name"),
                    "arguments": tool_call.get("function", {}).get("arguments"),
                })

        has_more = finish_reason is None

        return AIResponse(
            text=text if text else None,
            tool_calls=tool_calls,
            has_more=has_more,
        )

    @property
    def supports_native_audio(self) -> bool:
        """Grok is text-only, no native audio support."""
        return False

    @property
    def supports_function_calls(self) -> bool:
        """Grok supports function calls."""
        return True
