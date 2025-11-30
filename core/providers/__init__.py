"""AI provider interface and implementations for pluggable AI backends.

This module provides a provider-based architecture for AI, TTS, and STT services.

AI Providers:
  - OpenAI Realtime (native audio support)
  - Grok (text-based, requires TTS/STT)

TTS Providers:
  - OpenAI TTS
  - Local TTS (planned)

STT Providers:
  - OpenAI STT (Whisper)
  - Local STT (planned)
"""

from .ai_provider import (
    AIProvider,
    AIMessage,
    AIResponse,
    MessageRole,
    ToolDefinition,
    ToolCall,
    ProviderEvent,
    ProviderEventType,
)
from .openai_realtime import OpenAIRealtimeProvider
from .grok import GrokProvider
from .tts_provider import TTSProvider
from .stt_provider import STTProvider
from .openai_tts import OpenAITTSProvider
from .openai_stt import OpenAISTTProvider
from .factory import ProviderFactory

__all__ = [
    # AI Provider interfaces and types
    "AIProvider",
    "AIMessage",
    "AIResponse",
    "MessageRole",
    "ToolDefinition",
    "ToolCall",
    "ProviderEvent",
    "ProviderEventType",
    # AI Providers
    "OpenAIRealtimeProvider",
    "GrokProvider",
    # TTS/STT interfaces
    "TTSProvider",
    "STTProvider",
    # TTS/STT implementations
    "OpenAITTSProvider",
    "OpenAISTTProvider",
    # Factory
    "ProviderFactory",
]
