"""OpenAI Text-to-Speech provider."""

from typing import Optional
import httpx
from scipy.io import wavfile
import numpy as np
import io

from .tts_provider import TTSProvider
from core.config import OPENAI_API_KEY


class OpenAITTSProvider(TTSProvider):
    """TTS provider using OpenAI's API."""

    AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", "ballad"]
    DEFAULT_VOICE = "ballad"

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

    async def synthesize(
        self,
        text: str,
        voice: str = "ballad",
        speed: float = 1.0,
    ) -> bytes:
        """
        Synthesize text to speech using OpenAI API.

        Returns:
            Audio bytes in PCM format (24kHz, mono, int16)
        """
        if not self.client:
            raise RuntimeError("Provider not initialized")

        if voice not in self.AVAILABLE_VOICES:
            voice = self.DEFAULT_VOICE

        # Call OpenAI TTS API
        response = await self.client.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "tts-1",
                "input": text,
                "voice": voice,
                "speed": speed,
                "response_format": "wav",
            },
        )

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI API error: {response.text}")

        # Convert WAV to PCM 24kHz mono int16
        return self._convert_to_pcm(response.content)

    def _convert_to_pcm(self, wav_bytes: bytes) -> bytes:
        """Convert WAV audio to PCM 24kHz mono int16."""
        # Load WAV file
        wav_io = io.BytesIO(wav_bytes)
        sample_rate, audio_data = wavfile.read(wav_io)

        # Convert stereo to mono if needed
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample to 24kHz if needed
        if sample_rate != 24000:
            from scipy.signal import resample
            num_samples = int(len(audio_data) * 24000 / sample_rate)
            audio_data = resample(audio_data, num_samples).astype(np.int16)
        else:
            audio_data = audio_data.astype(np.int16)

        # Convert to bytes
        return audio_data.tobytes()

    @property
    def available_voices(self) -> list[str]:
        """Get list of available OpenAI voices."""
        return self.AVAILABLE_VOICES

    @property
    def default_voice(self) -> str:
        """Get default voice."""
        return self.DEFAULT_VOICE

    @property
    def output_sample_rate(self) -> int:
        """Output is 24kHz mono PCM."""
        return 24000

    @property
    def output_channels(self) -> int:
        """Output is mono."""
        return 1
