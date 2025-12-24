# Register realtime AI providers
print("DEBUG: Importing core.providers")
from .openai_provider import OpenAIProvider
from .xai_provider import XAIProvider
from ..realtime_ai_provider import voice_provider_registry
from ..config import OPENAI_API_KEY, OPENAI_MODEL, XAI_API_KEY

print(f"DEBUG: OPENAI_API_KEY set: {bool(OPENAI_API_KEY)}")
print(f"DEBUG: XAI_API_KEY set: {bool(XAI_API_KEY)}")

# Register the OpenAI provider
if OPENAI_API_KEY:
    openai_provider = OpenAIProvider(api_key=OPENAI_API_KEY, model=OPENAI_MODEL)
    voice_provider_registry.register_provider(openai_provider)
    print("DEBUG: OpenAI provider registered")
else:
    print("DEBUG: OpenAI provider not registered - no API key")

# Register the XAI provider
if XAI_API_KEY:
    xai_provider = XAIProvider(api_key=XAI_API_KEY)
    voice_provider_registry.register_provider(xai_provider)
    print("DEBUG: XAI provider registered")
else:
    print("DEBUG: XAI provider not registered - no API key")

print("DEBUG: Providers registered successfully")