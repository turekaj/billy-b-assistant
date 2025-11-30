"""OpenAI Realtime API provider with native audio support."""

import json
import asyncio
from typing import Optional, AsyncIterator
import websockets
import base64

from .ai_provider import (
    AIProvider,
    AIMessage,
    AIResponse,
    MessageRole,
    ToolDefinition,
)
from core.config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIRealtimeProvider(AIProvider):
    """Provider using OpenAI's Realtime API with native TTS/STT."""

    def __init__(self, model: str = OPENAI_MODEL):
        self.model = model
        self.api_key = OPENAI_API_KEY
        self.ws = None
        self._message_id = 0

    async def initialize(self) -> None:
        """Connect to OpenAI Realtime API."""
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        self.ws = await websockets.asyncio.client.connect(uri, additional_headers=headers)

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()

    async def send_message(
        self,
        message: AIMessage,
        conversation_history: list[AIMessage],
        system_prompt: str,
        tools: Optional[list[ToolDefinition]] = None,
    ) -> AsyncIterator[AIResponse]:
        """
        Send message via OpenAI Realtime API and stream responses.

        For OpenAI Realtime:
        - Audio is streamed natively (no separate TTS/STT needed)
        - Function calls are supported
        - Session is bidirectional with real-time audio
        """
        if not self.ws:
            raise RuntimeError("Provider not initialized")

        # Convert tools to OpenAI format
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

        # Send session configuration
        await self.ws.send(
            json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "instructions": system_prompt,
                    "tools": tools_config or [],
                    "audio": {
                        "input": {
                            "format": {"type": "audio/pcm", "rate": 24000},
                            "turn_detection": {"type": "server_vad"},
                        },
                        "output": {
                            "format": {"type": "audio/pcm", "rate": 24000},
                        },
                    },
                },
            })
        )

        # Handle audio input if provided
        if message.audio_bytes:
            # Send audio data to API
            audio_b64 = base64.b64encode(message.audio_bytes).decode()
            await self.ws.send(
                json.dumps({
                    "type": "input_audio_buffer.append",
                    "audio": audio_b64,
                })
            )

        # Send text message if provided
        if message.content:
            await self.ws.send(
                json.dumps({
                    "type": "conversation.item.create",
                    "item": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "text", "text": message.content}],
                    },
                })
            )

        # Trigger response generation
        await self.ws.send(json.dumps({"type": "response.create"}))

        # Stream responses
        async for message in self.ws:
            data = json.loads(message)
            yield self._process_response(data)

    def _process_response(self, data: dict) -> AIResponse:
        """Convert OpenAI Realtime message to AIResponse."""
        msg_type = data.get("type", "")

        if msg_type == "response.output_audio.delta":
            # Audio chunk from API
            audio_b64 = data.get("delta", "")
            audio_bytes = base64.b64decode(audio_b64) if audio_b64 else None
            return AIResponse(audio_bytes=audio_bytes, has_more=True)

        elif msg_type == "response.output_audio_transcript.delta":
            # Text chunk from API
            text = data.get("delta", "")
            return AIResponse(text=text, has_more=True)

        elif msg_type == "response.function_call_arguments.done":
            # Tool call from AI
            func_call = data.get("item", {})
            tool_calls = []
            if func_call.get("type") == "function":
                tool_calls.append({
                    "name": func_call.get("name"),
                    "arguments": func_call.get("arguments"),
                })
            return AIResponse(tool_calls=tool_calls, has_more=False)

        elif msg_type == "response.done":
            # Response complete
            return AIResponse(has_more=False)

        else:
            # Pass through other message types
            return AIResponse(has_more=True)

    @property
    def supports_native_audio(self) -> bool:
        """OpenAI Realtime has native audio support."""
        return True

    @property
    def supports_function_calls(self) -> bool:
        """OpenAI Realtime supports function calls."""
        return True
