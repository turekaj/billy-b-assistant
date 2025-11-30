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
    ProviderEvent,
    ProviderEventType,
    ToolCall,
)
from core.config import OPENAI_API_KEY, OPENAI_MODEL


class OpenAIRealtimeProvider(AIProvider):
    """Provider using OpenAI's Realtime API with native TTS/STT."""

    def __init__(self, model: str = OPENAI_MODEL):
        self.model = model
        self.api_key = OPENAI_API_KEY
        self.ws = None
        self._message_id = 0
        self._event_queue = asyncio.Queue()
        self._ws_read_task = None
        self._session_initialized = False

    async def initialize(self) -> None:
        """Connect to OpenAI Realtime API (background task starts when receive_events called)."""
        from core.logger import logger
        uri = f"wss://api.openai.com/v1/realtime?model={self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        logger.info(f"Connecting to OpenAI Realtime: {uri}", "🔌")
        self.ws = await websockets.asyncio.client.connect(uri, additional_headers=headers)
        logger.success("Connected to OpenAI Realtime WebSocket", "✅")
        logger.info("Provider initialized and ready", "✨")

    async def close(self) -> None:
        """Close WebSocket connection and background tasks."""
        if self._ws_read_task and not self._ws_read_task.done():
            self._ws_read_task.cancel()
            try:
                await self._ws_read_task
            except asyncio.CancelledError:
                pass

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

    @property
    def supports_server_vad(self) -> bool:
        """OpenAI Realtime supports server-side voice activity detection."""
        return True

    # Realtime provider interface implementations

    async def update_session(
        self,
        instructions: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        voice: Optional[str] = None
    ) -> None:
        """Update session configuration mid-conversation."""
        if not self.ws:
            raise RuntimeError("Provider not initialized")

        # Convert tools to OpenAI format if provided
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

        # Build session update
        session_update = {}
        if instructions is not None:
            session_update["instructions"] = instructions
        if tools_config is not None:
            session_update["tools"] = tools_config
        if voice is not None:
            session_update["voice"] = voice

        # Only send if there's something to update
        if session_update:
            await self.ws.send(
                json.dumps({
                    "type": "session.update",
                    "session": session_update,
                })
            )

    async def send_audio(self, audio_pcm: bytes) -> None:
        """Send raw PCM audio to provider."""
        if not self.ws:
            raise RuntimeError("Provider not initialized")

        # Encode audio as base64 and send to OpenAI
        audio_b64 = base64.b64encode(audio_pcm).decode("utf-8")
        await self.ws.send(
            json.dumps({
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
            })
        )

    async def receive_events(self) -> AsyncIterator[ProviderEvent]:
        """Receive events from provider event queue."""
        # Start background task on first call (after session config has been sent)
        if not self._ws_read_task:
            from core.logger import logger
            logger.info("Starting background message processing task", "🔄")
            self._ws_read_task = asyncio.create_task(self._process_ws_messages())

        while True:
            event = await self._event_queue.get()
            yield event

    async def send_tool_result(self, tool_call_id: str, result: dict) -> None:
        """Send tool execution result back to provider."""
        if not self.ws:
            raise RuntimeError("Provider not initialized")

        # OpenAI Realtime expects tool result to be sent via conversation.item.create
        await self.ws.send(
            json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "function_call_output",
                    "call_id": tool_call_id,
                    "output": json.dumps(result),
                },
            })
        )

    async def trigger_response(self) -> None:
        """Manually trigger a response from the provider."""
        if not self.ws:
            raise RuntimeError("Provider not initialized")

        # Send response.create to trigger AI response
        await self.ws.send(json.dumps({"type": "response.create"}))

    async def send_user_message(self, text: str) -> None:
        """Send a text message from user."""
        if not self.ws:
            raise RuntimeError("Provider not initialized")

        # Send user message via conversation.item.create
        await self.ws.send(
            json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "text", "text": text}],
                },
            })
        )

    async def _process_ws_messages(self) -> None:
        """Background task: read WebSocket messages and translate to ProviderEvent."""
        try:
            if not self.ws:
                return

            async for message in self.ws:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "unknown")
                    from core.logger import logger
                    logger.info(f"Received OpenAI message: {msg_type}", "📨")
                    event = self._translate_message(data)
                    if event:
                        logger.info(f"Translated to event: {event.type}", "✅")
                        await self._event_queue.put(event)
                    else:
                        # Log unhandled message types for debugging
                        logger.warning(f"Unhandled OpenAI message type: {msg_type} (returned None)", "⚠️")
                except json.JSONDecodeError:
                    # Skip malformed JSON messages
                    continue
                except asyncio.CancelledError:
                    break
        except Exception as e:
            # WebSocket connection closed or other error
            from core.logger import logger
            logger.error(f"WebSocket processing error: {type(e).__name__}: {e}", "❌")
            # Emit error event
            await self._event_queue.put(ProviderEvent(
                type=ProviderEventType.ERROR.value,
                data={"message": f"WebSocket error: {e}"}
            ))

    def _translate_message(self, data: dict) -> Optional[ProviderEvent]:
        """Translate OpenAI Realtime message to provider-agnostic ProviderEvent."""
        msg_type = data.get("type", "")

        # Audio output
        if msg_type == "response.output_audio.delta":
            audio_b64 = data.get("delta", "")
            audio_bytes = base64.b64decode(audio_b64) if audio_b64 else b""
            return ProviderEvent(
                type=ProviderEventType.AUDIO_OUT.value,
                data={"audio": audio_bytes}
            )

        # Transcript output
        elif msg_type == "response.output_audio_transcript.delta":
            text = data.get("delta", "")
            return ProviderEvent(
                type=ProviderEventType.TRANSCRIPT_DELTA.value,
                data={"text": text}
            )

        elif msg_type == "response.output_audio_transcript.done":
            text = data.get("transcript", "")
            return ProviderEvent(
                type=ProviderEventType.TRANSCRIPT_DONE.value,
                data={"text": text}
            )

        # Alternate transcript types (text-only mode)
        elif msg_type == "response.text.delta":
            text = data.get("delta", "")
            return ProviderEvent(
                type=ProviderEventType.TRANSCRIPT_DELTA.value,
                data={"text": text}
            )

        elif msg_type == "response.text.done":
            text = data.get("text", "")
            return ProviderEvent(
                type=ProviderEventType.TRANSCRIPT_DONE.value,
                data={"text": text}
            )

        # Tool call (function call)
        elif msg_type == "response.function_call_arguments.delta":
            # Delta updates to function call arguments - aggregate them
            # This is handled in response.function_call_arguments.done
            return None

        elif msg_type == "response.function_call_arguments.done":
            # Tool call is complete
            item = data.get("item", {})
            if item.get("type") == "function_call":
                call_id = item.get("id", "")
                function = item.get("function", {})
                arguments_str = function.get("arguments", "{}")
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    arguments = {}

                return ProviderEvent(
                    type=ProviderEventType.TOOL_CALL.value,
                    data={
                        "tool_call": ToolCall(
                            id=call_id,
                            name=function.get("name", ""),
                            arguments=arguments
                        )
                    }
                )

        # Speech detection
        elif msg_type == "input_audio_buffer.speech_started":
            return ProviderEvent(
                type=ProviderEventType.SPEECH_STARTED.value,
                data={}
            )

        elif msg_type == "input_audio_buffer.speech_stopped":
            return ProviderEvent(
                type=ProviderEventType.SPEECH_STOPPED.value,
                data={}
            )

        # Session updated
        elif msg_type in ("session.updated", "session_updated"):
            return ProviderEvent(
                type=ProviderEventType.SESSION_READY.value,
                data={}
            )

        # Response complete
        elif msg_type == "response.done":
            return ProviderEvent(
                type=ProviderEventType.RESPONSE_DONE.value,
                data={}
            )

        # Ignore other message types for now
        return None
