"""OpenAI Speech-to-Text provider."""

from typing import AsyncIterator
import httpx
import io

from .stt_provider import STTProvider
from core.config import OPENAI_API_KEY


class OpenAISTTProvider(STTProvider):
    """STT provider using OpenAI's Whisper API."""

    def __init__(self, api_key: str = OPENAI_API_KEY):
        self.api_key = api_key
        self.client = None

    async def initialize(self) -> None:
        """Initialize HTTP client for OpenAI API."""
        self.client = httpx.AsyncClient()

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    async def transcribe_stream(
        self,
        audio_chunks: AsyncIterator[bytes],
    ) -> AsyncIterator[str]:
        """
        Transcribe streaming audio using OpenAI Whisper API.

        Note: Whisper API doesn't support true streaming, so this
        accumulates chunks until done and transcribes complete audio.
        """
        if not self.client:
            raise RuntimeError("Provider not initialized")

        # Accumulate audio chunks (Whisper doesn't support streaming)
        audio_buffer = b""
        async for chunk in audio_chunks:
            audio_buffer += chunk

        if not audio_buffer:
            return

        # Transcribe complete audio
        files = {
            "file": ("audio.wav", io.BytesIO(audio_buffer), "audio/wav"),
        }

        response = await self.client.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            files=files,
            data={"model": "whisper-1"},
        )

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI Whisper API error: {response.text}")

        result = response.json()
        text = result.get("text", "")

        if text:
            yield text

    @property
    def input_sample_rate(self) -> int:
        """Whisper accepts 24kHz input."""
        return 24000

    @property
    def input_channels(self) -> int:
        """Whisper accepts mono input."""
        return 1

    @property
    def chunk_size_ms(self) -> int:
        """Recommended chunk size for streaming."""
        return 40
