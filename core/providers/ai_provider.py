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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
