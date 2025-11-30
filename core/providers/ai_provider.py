"""Abstract base class for AI providers."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Callable, AsyncIterator
from dataclasses import dataclass
from enum import Enum


class MessageRole(Enum):
    """Message role in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ProviderEventType(Enum):
    """Types of events from AI providers."""
    SESSION_READY = "session_ready"
    SPEECH_STARTED = "speech_started"
    SPEECH_STOPPED = "speech_stopped"
    AUDIO_OUT = "audio_out"
    TRANSCRIPT_DELTA = "transcript_delta"
    TRANSCRIPT_DONE = "transcript_done"
    TOOL_CALL = "tool_call"
    RESPONSE_DONE = "response_done"
    ERROR = "error"


class ToolType(Enum):
    """Type of tool/function the AI can call."""
    FUNCTION = "function"


@dataclass
class ToolDefinition:
    """Definition of a tool/function the AI can call."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema format


@dataclass
class ToolCall:
    """Provider-agnostic representation of a tool/function call."""
    id: str  # Unique identifier for this tool call
    name: str  # Name of the tool/function to call
    arguments: Dict[str, Any]  # Arguments to pass to the tool


@dataclass
class ProviderEvent:
    """Provider-agnostic event from AI."""
    type: str  # Event type (use ProviderEventType values)
    data: Dict[str, Any]  # Event-specific data


@dataclass
class AIMessage:
    """Message in conversation with AI."""
    role: MessageRole
    content: Optional[str] = None  # Text content
    audio_bytes: Optional[bytes] = None  # Audio content (base64 encoded)
    tool_name: Optional[str] = None  # For tool call messages
    tool_arguments: Optional[Dict[str, Any]] = None  # For tool call messages


@dataclass
class AIResponse:
    """Response from AI provider."""
    text: Optional[str] = None  # Text content of response
    audio_bytes: Optional[bytes] = None  # Audio bytes (for TTS-enabled providers)
    tool_calls: Optional[list] = None  # List of tool calls: [{name, arguments}]
    has_more: bool = False  # Indicates stream is not complete


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (e.g., connect to API)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass

    @abstractmethod
    async def send_message(
        self,
        message: AIMessage,
        conversation_history: list[AIMessage],
        system_prompt: str,
        tools: Optional[list[ToolDefinition]] = None,
    ) -> AsyncIterator[AIResponse]:
        """
        Send a message to the AI and get streamed responses.

        Args:
            message: The message to send
            conversation_history: Previous messages in conversation
            system_prompt: System-level instructions
            tools: Available tools/functions the AI can call

        Yields:
            AIResponse objects as they stream in
        """
        pass

    @property
    @abstractmethod
    def supports_native_audio(self) -> bool:
        """Whether this provider handles TTS/STT natively (like OpenAI Realtime)."""
        pass

    @property
    @abstractmethod
    def supports_function_calls(self) -> bool:
        """Whether this provider supports function calling."""
        pass

    @property
    @abstractmethod
    def supports_server_vad(self) -> bool:
        """Whether this provider supports server-side voice activity detection."""
        pass

    # Realtime provider interface methods
    # These are for providers that need bidirectional communication (realtime audio, events)

    @abstractmethod
    async def update_session(
        self,
        instructions: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        voice: Optional[str] = None
    ) -> None:
        """
        Update session configuration mid-conversation.

        Args:
            instructions: System instructions/prompt
            tools: Available tools/functions
            voice: Voice preference for TTS output
        """
        pass

    @abstractmethod
    async def send_audio(self, audio_pcm: bytes) -> None:
        """
        Send raw PCM audio to provider.

        Args:
            audio_pcm: Raw audio bytes in PCM format (24kHz mono int16)
        """
        pass

    @abstractmethod
    async def receive_events(self) -> AsyncIterator[ProviderEvent]:
        """
        Receive events from provider.

        Yields:
            ProviderEvent objects (audio, transcripts, tool calls, etc)
        """
        pass

    @abstractmethod
    async def send_tool_result(self, tool_call_id: str, result: Dict[str, Any]) -> None:
        """
        Send tool execution result back to provider.

        Args:
            tool_call_id: ID of the tool call this result is for
            result: Result dictionary with status and data
        """
        pass

    @abstractmethod
    async def trigger_response(self) -> None:
        """
        Manually trigger a response from the provider.

        Used for kickoff messages and post-tool execution.
        """
        pass

    @abstractmethod
    async def send_user_message(self, text: str) -> None:
        """
        Send a text message from user.

        Args:
            text: The user's message text
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
