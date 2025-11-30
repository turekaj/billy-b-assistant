"""Unit tests for OpenAI Realtime provider."""

import pytest
from core.providers import (
    OpenAIRealtimeProvider,
    AIMessage,
    AIResponse,
    MessageRole,
    ToolDefinition,
)


class TestOpenAIRealtimeProvider:
    """Tests for OpenAIRealtimeProvider."""

    def test_provider_properties(self):
        """Test provider reports correct capabilities."""
        provider = OpenAIRealtimeProvider()

        assert provider.supports_native_audio is True
        assert provider.supports_function_calls is True
        assert str(provider) == "OpenAIRealtimeProvider()"

    def test_provider_initialization(self):
        """Test provider can be instantiated with config."""
        provider = OpenAIRealtimeProvider(model="gpt-realtime-mini")
        assert provider.model == "gpt-realtime-mini"

    def test_default_model(self):
        """Test provider uses default model from config."""
        provider = OpenAIRealtimeProvider()
        # Should use OPENAI_MODEL from config
        assert provider.model is not None

    def test_message_creation(self):
        """Test AIMessage objects can be created."""
        # Text message
        msg = AIMessage(role=MessageRole.USER, content="Hello")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"
        assert msg.audio_bytes is None

        # Audio message
        audio_bytes = b"\x00\x01\x02\x03"
        msg = AIMessage(role=MessageRole.USER, audio_bytes=audio_bytes)
        assert msg.audio_bytes == audio_bytes
        assert msg.content is None

    def test_tool_definition(self):
        """Test ToolDefinition objects."""
        tool = ToolDefinition(
            name="play_song",
            description="Play a song",
            parameters={
                "type": "object",
                "properties": {"song_name": {"type": "string"}},
                "required": ["song_name"],
            },
        )

        assert tool.name == "play_song"
        assert tool.description == "Play a song"
        assert "song_name" in tool.parameters["properties"]

    def test_ai_response_variants(self):
        """Test AIResponse can carry different types of data."""
        # Text response
        resp = AIResponse(text="Hello", has_more=True)
        assert resp.text == "Hello"
        assert resp.audio_bytes is None
        assert resp.tool_calls is None
        assert resp.has_more is True

        # Audio response
        audio = b"\x00\x01"
        resp = AIResponse(audio_bytes=audio, has_more=True)
        assert resp.audio_bytes == audio
        assert resp.text is None

        # Tool call response
        resp = AIResponse(
            tool_calls=[{"name": "play_song", "arguments": {"song": "test"}}],
            has_more=False,
        )
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0]["name"] == "play_song"

    def test_message_roles(self):
        """Test all message roles."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"

    def test_response_streaming_pattern(self):
        """Test typical response streaming pattern."""
        responses = [
            AIResponse(text="Hello", has_more=True),
            AIResponse(text=" world", has_more=True),
            AIResponse(has_more=False),
        ]

        # Simulate streaming
        full_text = ""
        for resp in responses:
            if resp.text:
                full_text += resp.text
            if not resp.has_more:
                break

        assert full_text == "Hello world"

    def test_response_with_tool_calls(self):
        """Test response with tool calls."""
        resp = AIResponse(
            text="Playing song",
            tool_calls=[
                {
                    "name": "play_song",
                    "arguments": {"title": "Imagine", "artist": "John Lennon"},
                }
            ],
            has_more=False,
        )

        assert resp.text == "Playing song"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0]["arguments"]["title"] == "Imagine"

    def test_multiple_tool_calls(self):
        """Test response with multiple tool calls."""
        resp = AIResponse(
            tool_calls=[
                {"name": "play_song", "arguments": {"title": "Song 1"}},
                {"name": "store_memory", "arguments": {"memory": "User likes music"}},
            ],
            has_more=False,
        )

        assert len(resp.tool_calls) == 2
        assert resp.tool_calls[0]["name"] == "play_song"
        assert resp.tool_calls[1]["name"] == "store_memory"
