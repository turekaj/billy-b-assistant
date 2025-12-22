# Register realtime AI providers
from .openai_provider import OpenAIProvider
from ..realtime_ai_provider import voice_provider_registry
from ..config import OPENAI_API_KEY, OPENAI_MODEL

# Register the OpenAI provider
openai_provider = OpenAIProvider(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)
voice_provider_registry.register_provider(openai_provider)