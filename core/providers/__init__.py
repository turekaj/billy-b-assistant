"""AI provider interface and implementations for pluggable AI backends.

This module provides a provider-based architecture for AI, TTS, and STT services.
Current implementation: OpenAI Realtime (native audio support)
Future implementations: Grok, Claude, and others in _future/ directory
"""

from .ai_provider import AIProvider, AIMessage, AIResponse, MessageRole, ToolDefinition
from .openai_realtime import OpenAIRealtimeProvider

__all__ = [
    "AIProvider",
    "AIMessage",
    "AIResponse",
    "MessageRole",
    "ToolDefinition",
    "OpenAIRealtimeProvider",
]
