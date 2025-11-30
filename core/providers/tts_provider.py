"""Abstract base class for Text-to-Speech providers."""

from abc import ABC, abstractmethod
from typing import Optional


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the TTS provider (e.g., connect to API)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = "default",
        speed: float = 1.0,
    ) -> bytes:
        """
        Synthesize text to speech audio.

        Args:
            text: Text to synthesize
            voice: Voice identifier (provider-specific)
            speed: Speech speed multiplier (1.0 = normal)

        Returns:
            Audio bytes in PCM format (24kHz, mono, int16)
        """
        pass

    @property
    @abstractmethod
    def available_voices(self) -> list[str]:
        """Get list of available voices."""
        pass

    @property
    @abstractmethod
    def default_voice(self) -> str:
        """Get default voice identifier."""
        pass

    @property
    @abstractmethod
    def output_sample_rate(self) -> int:
        """Output sample rate in Hz (typically 24000)."""
        pass

    @property
    @abstractmethod
    def output_channels(self) -> int:
        """Number of audio channels (typically 1 for mono)."""
        pass
