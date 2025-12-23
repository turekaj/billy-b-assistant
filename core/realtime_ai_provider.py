from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class RealtimeAIProvider(ABC):
    @abstractmethod
    async def generate_audio_clip(self, prompt: str, voice: Optional[str] = None, instructions: Optional[str] = None, **kwargs) -> bytes:
        """Generate audio clip from text prompt using specified voice or default"""
        pass

    @abstractmethod
    def get_supported_voices(self) -> list[str]:
        """Return list of supported voice names"""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider identifier"""
        pass

    @abstractmethod
    def get_connection_uri(self) -> str:
        """Return the WebSocket URI for realtime connection"""
        pass

    @abstractmethod
    def get_headers(self) -> dict:
        """Return headers for WebSocket connection"""
        pass

    @abstractmethod
    def get_session_config(self, instructions: str, tools: Optional[List[Dict[str, Any]]] = None, voice: Optional[str] = None, text_only: bool = False, vad_params: Optional[Dict[str, Any]] = None) -> dict:
        """Return the session configuration dict for realtime session.update"""
        pass

    @property
    @abstractmethod
    def default_voice(self) -> str:
        """Return the default voice for this provider"""
        pass




class RealtimeAIProviderRegistry:
    def __init__(self):
        self.providers: Dict[str, RealtimeAIProvider] = {}
        self.default_provider: Optional[str] = None

    def register_provider(self, provider: RealtimeAIProvider):
        """Register a voice provider"""
        name = provider.get_provider_name()
        self.providers[name] = provider
        if self.default_provider is None:
            self.default_provider = name

    def get_provider(self, name: Optional[str] = None) -> RealtimeAIProvider:
        """Get a voice provider by name, or default if none specified"""
        if name is None:
            name = self.default_provider
        if name not in self.providers:
            raise ValueError(f"Voice provider '{name}' not found")
        return self.providers[name]

    def get_available_providers(self) -> list[str]:
        """Return list of available provider names"""
        return list(self.providers.keys())

    def set_default_provider(self, name: str):
        """Set the default voice provider"""
        if name not in self.providers:
            raise ValueError(f"Voice provider '{name}' not found")
        self.default_provider = name


# Global registry instance
voice_provider_registry = RealtimeAIProviderRegistry()