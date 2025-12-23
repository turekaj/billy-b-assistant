from typing import Optional

from ..config import OPENAI_API_KEY, OPENAI_MODEL, VOICE_PROVIDER, XAI_API_KEY, XAI_VOICE
from .openai_provider import OpenAIProvider
from .xai_provider import XAIProvider


def get_voice_provider(voice: Optional[str] = None):
    """Get the appropriate voice provider based on VOICE_PROVIDER config."""
    if VOICE_PROVIDER == "xai":
        if not XAI_API_KEY:
            raise ValueError("XAI_API_KEY not set in environment")
        return XAIProvider(api_key=XAI_API_KEY, voice=voice or XAI_VOICE)
    elif VOICE_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment")
        return OpenAIProvider(api_key=OPENAI_API_KEY, model=OPENAI_MODEL, voice=voice)
    else:
        raise ValueError(f"Unsupported VOICE_PROVIDER: {VOICE_PROVIDER}")