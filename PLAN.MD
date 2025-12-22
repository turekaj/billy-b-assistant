# Realtime AI Provider Abstraction Plan

## Overview

This plan outlines the abstraction of OpenAI realtime AI functionality into a modular `RealtimeAIProvider` class system. The goal is to decouple voice synthesis from specific providers, enabling runtime selection of voice providers and future extensibility to add new providers like XAI voice API.

## Current State Analysis

### Voice Usage in Codebase

- **Primary Usage**: Voice functionality is currently implemented in `core/wakeup.py` via the `WakeupClipGenerator` class
- **API Used**: OpenAI Realtime API (`wss://api.openai.com/v1/realtime`) for generating wake-up audio clips
- **Configuration**: Voice selection is done via persona settings, defaulting to "ballad" voice
- **Functionality**: Generates audio clips by sending text prompts and receiving PCM audio data via WebSocket

### Hardcoded Dependencies

- Direct OpenAI API calls in `WakeupClipGenerator.generate()`
- Hardcoded WebSocket URI, headers, and session configuration
- No abstraction layer for different voice providers

## Design

### RealtimeAIProvider Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

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

    @property
    @abstractmethod
    def default_voice(self) -> str:
        """Return the default voice for this provider"""
        pass
```

### Provider Registry

- Create a `VoiceProviderRegistry` class to manage available providers
- Support runtime provider selection via configuration
- Default to OpenAI provider for backward compatibility

### Configuration Integration

- Add `VOICE_PROVIDER` setting to config
- Runtime selectable via webconfig settings form
- Support for provider-specific configuration (API keys, endpoints, etc.)

## Implementation Steps

### Phase 1: Core Abstraction

1. **Create RealtimeAIProvider Base Class** (`core/realtime_ai_provider.py`)
   - Define abstract interface
   - Include common utilities for audio processing

2. **Implement OpenAI Provider** (`core/providers/openai_provider.py`)
   - Extract current OpenAI logic from WakeupClipGenerator
   - Implement RealtimeAIProvider interface
   - Maintain all existing functionality

3. **Create Provider Registry** (`core/realtime_ai_provider_registry.py`)
   - Manage provider instances
   - Handle provider selection and initialization

### Phase 2: Integration

4. **Update WakeupClipGenerator**
   - Replace hardcoded OpenAI calls with VoiceProvider usage
   - Inject provider via constructor or factory method
   - Maintain backward compatibility

5. **Add Configuration Support**
   - Update `core/config.py` with VOICE_PROVIDER setting
   - Add provider selection to webconfig settings form
   - Implement runtime provider switching

### Phase 3: Extensibility

6. **Prepare for Future Providers**
   - Document provider interface requirements
   - Create template for new provider implementations
   - Consider XAI voice API integration patterns

## File Structure

```
core/
├── realtime_ai_provider.py                 # Abstract base class
├── realtime_ai_provider_registry.py       # Provider management
├── providers/
│   ├── __init__.py
│   └── openai_provider.py     # OpenAI implementation
└── wakeup.py                         # Updated to use abstraction
```

## Configuration

Add to `core/config.py`:

```python
VOICE_PROVIDER = os.getenv("VOICE_PROVIDER", "openai")
VOICE_PROVIDERS = {
    "openai": {
        "api_key": OPENAI_API_KEY,
        "model": OPENAI_MODEL,
    }
}
```

## Future Extensions

### XAI Voice Provider ✅

- ✅ Implement `XAIVoiceProvider` class
- ✅ Add XAI API integration
- ✅ Update provider registry to include XAI option
- ✅ Add configuration support (XAI_API_KEY, VOICE_PROVIDER=xai)

### Additional Providers

- ElevenLabs
- Azure TTS
- Local TTS engines
- Custom provider implementations

### Advanced Features

- Voice quality comparison
- Provider failover
- Voice caching and optimization
- Multi-language support

## Testing Strategy

### Unit Tests

- Test VoiceProvider interface compliance
- Mock provider implementations
- Test provider registry functionality

### Integration Tests

- Verify WakeupClipGenerator works with different providers
- Test configuration loading and provider selection
- Ensure backward compatibility

### Manual Testing

- Test audio clip generation with OpenAI provider
- Verify settings form updates provider selection
- Confirm runtime switching works without restart

## Migration Path

1. Implement abstraction with OpenAI as default
2. Deploy changes ensuring no breaking changes
3. Add new providers incrementally
4. Update documentation and user guides

## Success Criteria

- [ ] Existing functionality preserved
- [ ] Runtime provider selection works
- [ ] OpenAI provider produces identical results
- [ ] Configuration UI allows provider selection
- [ ] Code is extensible for new providers
- [ ] No performance degradation

## Timeline

- Phase 1: 2-3 days
- Phase 2: 2-3 days  
- Phase 3: 1-2 days
- Testing: 1-2 days

## Risks and Mitigations

- **API Changes**: Monitor OpenAI API for breaking changes
- **Audio Quality**: Ensure abstraction doesn't affect audio output
- **Performance**: Profile and optimize provider switching
- **Configuration Errors**: Validate provider configurations at startup