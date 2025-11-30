"""Mock AI provider for testing provider abstraction."""

import asyncio
from typing import AsyncIterator, Dict, Any, Optional

from core.providers import (
    AIProvider,
    ProviderEvent,
    ProviderEventType,
    ToolCall,
    ToolDefinition,
)


class MockAIProvider(AIProvider):
    """Mock provider for testing BillySession abstraction."""

    def __init__(self):
        """Initialize mock provider."""
        self.initialized = False
        self.closed = False
        self.messages_sent = []
        self.audio_chunks_sent = []
        self.tool_results_sent = []
        self.responses_triggered = 0
        self.session_updates = []
        self._event_queue = asyncio.Queue()
        self._processing_task = None

    async def initialize(self) -> None:
        """Initialize the provider (mock: just set flag and emit session_ready)."""
        self.initialized = True
        await self._event_queue.put(ProviderEvent(
            type=ProviderEventType.SESSION_READY.value,
            data={}
        ))

    async def close(self) -> None:
        """Clean up resources (mock: just set flag)."""
        self.closed = True
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()

    async def send_message(
        self,
        message,
        conversation_history,
        system_prompt: str,
        tools: Optional[list[ToolDefinition]] = None,
    ) -> AsyncIterator:
        """Send message via mock (not used in realtime mode, just yield)."""
        yield None  # Mock doesn't use this in realtime mode

    async def update_session(
        self,
        instructions: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        voice: Optional[str] = None
    ) -> None:
        """Update session configuration (mock: record the update)."""
        self.session_updates.append({
            "instructions": instructions,
            "tools": tools,
            "voice": voice,
        })

    async def send_audio(self, audio_pcm: bytes) -> None:
        """Send raw PCM audio (mock: record the chunk)."""
        self.audio_chunks_sent.append(audio_pcm)

    async def receive_events(self) -> AsyncIterator[ProviderEvent]:
        """Receive events from provider (mock: yield from internal queue)."""
        while True:
            event = await self._event_queue.get()
            yield event

    async def send_tool_result(self, tool_call_id: str, result: Dict[str, Any]) -> None:
        """Send tool execution result (mock: record it)."""
        self.tool_results_sent.append({
            "tool_call_id": tool_call_id,
            "result": result,
        })

    async def trigger_response(self) -> None:
        """Manually trigger a response (mock: increment counter and emit event)."""
        self.responses_triggered += 1
        await self._event_queue.put(ProviderEvent(
            type=ProviderEventType.TRANSCRIPT_DELTA.value,
            data={"text": "[Mock response triggered]"}
        ))
        await self._event_queue.put(ProviderEvent(
            type=ProviderEventType.RESPONSE_DONE.value,
            data={}
        ))

    async def send_user_message(self, text: str) -> None:
        """Send a text message from user (mock: record it)."""
        self.messages_sent.append(text)

    @property
    def supports_native_audio(self) -> bool:
        """Whether this provider handles TTS/STT natively."""
        return True

    @property
    def supports_function_calls(self) -> bool:
        """Whether this provider supports function calling."""
        return True

    @property
    def supports_server_vad(self) -> bool:
        """Whether this provider supports server-side voice activity detection."""
        return True

    # Testing helper methods

    def inject_event(self, event: ProviderEvent) -> None:
        """Inject an event for testing (non-async, schedules the injection)."""
        asyncio.create_task(self._event_queue.put(event))

    def inject_audio_event(self, audio_bytes: bytes) -> None:
        """Inject an audio output event."""
        self.inject_event(ProviderEvent(
            type=ProviderEventType.AUDIO_OUT.value,
            data={"audio": audio_bytes}
        ))

    def inject_transcript_delta(self, text: str) -> None:
        """Inject a transcript delta event."""
        self.inject_event(ProviderEvent(
            type=ProviderEventType.TRANSCRIPT_DELTA.value,
            data={"text": text}
        ))

    def inject_transcript_done(self, text: str = "") -> None:
        """Inject a transcript done event."""
        self.inject_event(ProviderEvent(
            type=ProviderEventType.TRANSCRIPT_DONE.value,
            data={"text": text}
        ))

    def inject_tool_call(self, tool_id: str, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Inject a tool call event."""
        self.inject_event(ProviderEvent(
            type=ProviderEventType.TOOL_CALL.value,
            data={
                "tool_call": ToolCall(
                    id=tool_id,
                    name=tool_name,
                    arguments=arguments
                )
            }
        ))

    def inject_response_done(self) -> None:
        """Inject a response done event."""
        self.inject_event(ProviderEvent(
            type=ProviderEventType.RESPONSE_DONE.value,
            data={}
        ))

    def inject_error(self, error_type: str, message: str) -> None:
        """Inject an error event."""
        self.inject_event(ProviderEvent(
            type=ProviderEventType.ERROR.value,
            data={"error_type": error_type, "message": message}
        ))

    def clear_events(self) -> None:
        """Clear the event queue (for testing isolation)."""
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def reset(self) -> None:
        """Reset the mock provider to initial state."""
        self.initialized = False
        self.closed = False
        self.messages_sent = []
        self.audio_chunks_sent = []
        self.tool_results_sent = []
        self.responses_triggered = 0
        self.session_updates = []
        self.clear_events()
