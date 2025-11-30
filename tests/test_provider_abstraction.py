"""Tests for provider abstraction and event handling."""

import asyncio
import pytest
from tests.mock_provider import MockAIProvider
from core.providers import (
    ProviderEvent,
    ProviderEventType,
    ToolCall,
    ToolDefinition,
)


class TestMockProviderBasics:
    """Test MockAIProvider basic functionality."""

    def test_mock_provider_initialization(self):
        """Test mock provider initializes correctly."""
        provider = MockAIProvider()
        assert not provider.initialized
        assert not provider.closed

    def test_mock_provider_capabilities(self):
        """Test mock provider reports capabilities."""
        provider = MockAIProvider()

        assert provider.supports_native_audio is True
        assert provider.supports_function_calls is True
        assert provider.supports_server_vad is True

    def test_mock_provider_string_representation(self):
        """Test mock provider string representation."""
        provider = MockAIProvider()
        assert str(provider) == "MockAIProvider()"


class TestMockProviderEventHandling:
    """Test MockAIProvider event injection and processing."""

    def test_session_ready_event_on_init(self):
        """Test session_ready event is emitted on initialization."""
        async def _run_test():
            provider = MockAIProvider()
            await provider.initialize()

            # Get first event
            event = None
            async for evt in provider.receive_events():
                event = evt
                break

            assert event is not None
            assert event.type == ProviderEventType.SESSION_READY.value

        asyncio.run(_run_test())

    def test_inject_audio_event(self):
        """Test injecting audio output event."""
        async def _run_test():
            provider = MockAIProvider()
            audio_data = b"\x00\x01\x02\x03"
            provider.inject_audio_event(audio_data)

            # Wait a moment for async injection
            await asyncio.sleep(0.01)

            event = None
            async for evt in provider.receive_events():
                event = evt
                if event.type == ProviderEventType.AUDIO_OUT.value:
                    break

            assert event is not None
            assert event.type == ProviderEventType.AUDIO_OUT.value
            assert event.data["audio"] == audio_data

        asyncio.run(_run_test())

    def test_inject_transcript_events(self):
        """Test injecting transcript events."""
        async def _run_test():
            provider = MockAIProvider()
            provider.inject_transcript_delta("Hello")
            provider.inject_transcript_delta(" world")
            provider.inject_transcript_done()

            await asyncio.sleep(0.01)

            events = []
            event_iter = provider.receive_events()
            for _ in range(3):  # Collect 3 events
                events.append(await event_iter.__anext__())

            assert events[0].type == ProviderEventType.TRANSCRIPT_DELTA.value
            assert events[0].data["text"] == "Hello"
            assert events[1].type == ProviderEventType.TRANSCRIPT_DELTA.value
            assert events[1].data["text"] == " world"
            assert events[2].type == ProviderEventType.TRANSCRIPT_DONE.value

        asyncio.run(_run_test())

    def test_inject_tool_call(self):
        """Test injecting tool call event."""
        async def _run_test():
            provider = MockAIProvider()
            provider.inject_tool_call(
                tool_id="call-123",
                tool_name="play_song",
                arguments={"song": "Imagine"}
            )

            await asyncio.sleep(0.01)

            event = None
            async for evt in provider.receive_events():
                event = evt
                if event.type == ProviderEventType.TOOL_CALL.value:
                    break

            assert event is not None
            assert event.type == ProviderEventType.TOOL_CALL.value
            tool_call = event.data["tool_call"]
            assert isinstance(tool_call, ToolCall)
            assert tool_call.id == "call-123"
            assert tool_call.name == "play_song"
            assert tool_call.arguments["song"] == "Imagine"

        asyncio.run(_run_test())

    def test_inject_error_event(self):
        """Test injecting error event."""
        async def _run_test():
            provider = MockAIProvider()
            provider.inject_error("auth_error", "Invalid API key")

            await asyncio.sleep(0.01)

            event = None
            async for evt in provider.receive_events():
                event = evt
                if event.type == ProviderEventType.ERROR.value:
                    break

            assert event is not None
            assert event.type == ProviderEventType.ERROR.value
            assert event.data["error_type"] == "auth_error"
            assert event.data["message"] == "Invalid API key"

        asyncio.run(_run_test())


class TestMockProviderAudioHandling:
    """Test MockAIProvider audio handling."""

    def test_send_audio_records_chunks(self):
        """Test send_audio records audio chunks."""
        async def _run_test():
            provider = MockAIProvider()

            audio1 = b"\x00\x01\x02\x03"
            audio2 = b"\x04\x05\x06\x07"

            await provider.send_audio(audio1)
            await provider.send_audio(audio2)

            assert len(provider.audio_chunks_sent) == 2
            assert provider.audio_chunks_sent[0] == audio1
            assert provider.audio_chunks_sent[1] == audio2

        asyncio.run(_run_test())


class TestMockProviderMessageHandling:
    """Test MockAIProvider message handling."""

    def test_send_user_message_records_text(self):
        """Test send_user_message records messages."""
        async def _run_test():
            provider = MockAIProvider()

            await provider.send_user_message("Hello")
            await provider.send_user_message("How are you?")

            assert len(provider.messages_sent) == 2
            assert provider.messages_sent[0] == "Hello"
            assert provider.messages_sent[1] == "How are you?"

        asyncio.run(_run_test())


class TestMockProviderSessionUpdates:
    """Test MockAIProvider session configuration updates."""

    def test_update_session_records_config(self):
        """Test update_session records configuration."""
        async def _run_test():
            provider = MockAIProvider()
            tool = ToolDefinition(
                name="play_song",
                description="Play a song",
                parameters={"type": "object"}
            )

            await provider.update_session(
                instructions="Be helpful",
                tools=[tool],
                voice="nova"
            )

            assert len(provider.session_updates) == 1
            update = provider.session_updates[0]
            assert update["instructions"] == "Be helpful"
            assert update["tools"] == [tool]
            assert update["voice"] == "nova"

        asyncio.run(_run_test())

    def test_update_session_partial(self):
        """Test update_session with partial configuration."""
        async def _run_test():
            provider = MockAIProvider()

            await provider.update_session(instructions="Be helpful")
            await provider.update_session(voice="nova")

            assert len(provider.session_updates) == 2
            assert provider.session_updates[0]["instructions"] == "Be helpful"
            assert provider.session_updates[0]["tools"] is None
            assert provider.session_updates[1]["instructions"] is None
            assert provider.session_updates[1]["voice"] == "nova"

        asyncio.run(_run_test())


class TestMockProviderToolHandling:
    """Test MockAIProvider tool result handling."""

    def test_send_tool_result_records_result(self):
        """Test send_tool_result records results."""
        async def _run_test():
            provider = MockAIProvider()

            result1 = {"status": "success", "song": "Imagine"}
            result2 = {"status": "error", "message": "Song not found"}

            await provider.send_tool_result("call-1", result1)
            await provider.send_tool_result("call-2", result2)

            assert len(provider.tool_results_sent) == 2
            assert provider.tool_results_sent[0]["tool_call_id"] == "call-1"
            assert provider.tool_results_sent[0]["result"] == result1
            assert provider.tool_results_sent[1]["tool_call_id"] == "call-2"
            assert provider.tool_results_sent[1]["result"] == result2

        asyncio.run(_run_test())


class TestMockProviderResponseTrigger:
    """Test MockAIProvider response triggering."""

    def test_trigger_response_emits_events(self):
        """Test trigger_response emits transcript and response_done events."""
        async def _run_test():
            provider = MockAIProvider()

            await provider.trigger_response()
            assert provider.responses_triggered == 1

            await asyncio.sleep(0.01)

            events = []
            event_iter = provider.receive_events()
            for _ in range(2):  # Collect 2 events
                events.append(await event_iter.__anext__())

            assert events[0].type == ProviderEventType.TRANSCRIPT_DELTA.value
            assert events[1].type == ProviderEventType.RESPONSE_DONE.value

        asyncio.run(_run_test())

    def test_trigger_response_multiple_times(self):
        """Test trigger_response can be called multiple times."""
        async def _run_test():
            provider = MockAIProvider()

            await provider.trigger_response()
            await provider.trigger_response()
            await provider.trigger_response()

            assert provider.responses_triggered == 3

        asyncio.run(_run_test())


class TestMockProviderReset:
    """Test MockAIProvider reset and cleanup."""

    def test_reset_clears_state(self):
        """Test reset clears all recorded data."""
        async def _run_test():
            provider = MockAIProvider()
            await provider.initialize()

            await provider.send_user_message("Hello")
            await provider.send_audio(b"\x00\x01")
            await provider.send_tool_result("call-1", {"status": "ok"})
            await provider.update_session(instructions="Be helpful")
            await provider.trigger_response()

            assert provider.messages_sent
            assert provider.audio_chunks_sent
            assert provider.tool_results_sent
            assert provider.session_updates
            assert provider.responses_triggered > 0

            provider.reset()

            assert not provider.messages_sent
            assert not provider.audio_chunks_sent
            assert not provider.tool_results_sent
            assert not provider.session_updates
            assert provider.responses_triggered == 0
            assert not provider.initialized

        asyncio.run(_run_test())

    def test_clear_events_removes_queued_events(self):
        """Test clear_events removes all queued events."""
        async def _run_test():
            provider = MockAIProvider()

            provider.inject_audio_event(b"\x00\x01")
            provider.inject_transcript_delta("Hello")
            provider.inject_response_done()

            await asyncio.sleep(0.01)  # Let events be queued

            assert not provider._event_queue.empty()

            provider.clear_events()

            assert provider._event_queue.empty()

        asyncio.run(_run_test())
