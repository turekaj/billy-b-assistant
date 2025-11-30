"""Abstract base class for Speech-to-Text providers."""

from abc import ABC, abstractmethod
from typing import AsyncIterator


class STTProvider(ABC):
    """Abstract base class for STT providers."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the STT provider (e.g., connect to API)."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[str]:
        """
        Transcribe streaming audio to text.

        Args:
            audio_chunks: Async iterator of audio bytes (PCM, 24kHz, mono, int16)

        Yields:
            Transcribed text chunks as they arrive
        """
        pass

    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe complete audio to text.

        Args:
            audio_bytes: Audio bytes in PCM format (24kHz, mono, int16)

        Returns:
            Complete transcribed text
        """
        # Default implementation: convert bytes to chunk iterator
        async def chunk_iterator():
            yield audio_bytes

        result = ""
        async for chunk in self.transcribe_stream(chunk_iterator()):
            result += chunk
        return result

    @property
    @abstractmethod
    def input_sample_rate(self) -> int:
        """Input sample rate in Hz (typically 24000)."""
        pass

    @property
    @abstractmethod
    def input_channels(self) -> int:
        """Number of audio channels (typically 1 for mono)."""
        pass

    @property
    @abstractmethod
    def chunk_size_ms(self) -> int:
        """Recommended chunk size in milliseconds."""
        pass
