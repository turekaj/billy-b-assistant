"""Factory for creating AI, TTS, and STT provider instances."""

from typing import Optional

from .ai_provider import AIProvider
from .tts_provider import TTSProvider
from .stt_provider import STTProvider
from .openai_realtime import OpenAIRealtimeProvider
from .openai_tts import OpenAITTSProvider
from .openai_stt import OpenAISTTProvider
from .grok import GrokProvider


class ProviderFactory:
    """Factory for creating provider instances based on configuration."""

    @staticmethod
    def create_ai_provider(
        provider_name: str,
        openai_api_key: Optional[str] = None,
        openai_model: Optional[str] = None,
        grok_api_key: Optional[str] = None,
        grok_model: Optional[str] = None,
    ) -> AIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_name: "openai_realtime" or "grok"
            openai_api_key: API key for OpenAI (if using OpenAI provider)
            openai_model: Model name for OpenAI
            grok_api_key: API key for Grok (if using Grok provider)
            grok_model: Model name for Grok

        Returns:
            Initialized AIProvider instance
        """
        provider_name = provider_name.lower().strip()

        if provider_name == "openai_realtime":
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY required for openai_realtime provider")
            return OpenAIRealtimeProvider(
                model=openai_model or "gpt-realtime-mini"
            )

        elif provider_name == "grok":
            if not grok_api_key:
                raise ValueError("GROK_API_KEY required for grok provider")
            return GrokProvider(
                api_key=grok_api_key,
                model=grok_model or "grok-2",
            )

        else:
            raise ValueError(f"Unknown AI provider: {provider_name}")

    @staticmethod
    def create_tts_provider(
        provider_name: str,
        openai_api_key: Optional[str] = None,
    ) -> TTSProvider:
        """
        Create a TTS provider instance.

        Args:
            provider_name: "openai" or "local"
            openai_api_key: API key for OpenAI (if using OpenAI provider)

        Returns:
            Initialized TTSProvider instance
        """
        provider_name = provider_name.lower().strip()

        if provider_name == "openai":
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY required for openai TTS provider")
            return OpenAITTSProvider(api_key=openai_api_key)

        elif provider_name == "local":
            raise NotImplementedError("Local TTS provider not yet implemented")

        else:
            raise ValueError(f"Unknown TTS provider: {provider_name}")

    @staticmethod
    def create_stt_provider(
        provider_name: str,
        openai_api_key: Optional[str] = None,
    ) -> STTProvider:
        """
        Create an STT provider instance.

        Args:
            provider_name: "openai" or "local"
            openai_api_key: API key for OpenAI (if using OpenAI provider)

        Returns:
            Initialized STTProvider instance
        """
        provider_name = provider_name.lower().strip()

        if provider_name == "openai":
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY required for openai STT provider")
            return OpenAISTTProvider(api_key=openai_api_key)

        elif provider_name == "local":
            raise NotImplementedError("Local STT provider not yet implemented")

        else:
            raise ValueError(f"Unknown STT provider: {provider_name}")
