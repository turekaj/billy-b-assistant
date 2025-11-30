# AI Provider System

Billy-B Assistant uses a pluggable provider architecture for AI backends. This allows for future expansion to support multiple AI services and custom implementations.

**Current Release:** OpenAI Realtime provider with native audio support (achieving feature parity with previous implementation)
**Future:** Support for Grok, Claude, and other AI services with configurable TTS/STT providers

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   BillySession                              │
│  (orchestrates interaction flow)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌────────┐  ┌────────┐  ┌────────┐
    │   AI   │  │  TTS   │  │  STT   │
    │Provider│  │Provider│  │Provider│
    └────────┘  └────────┘  └────────┘
        │            │            │
    ┌───┴────────────┼────────────┴───┐
    │                │                │
    ▼                ▼                ▼
 OpenAI       OpenAI TTS        OpenAI STT
 Realtime     (Whisper)         (Whisper)
    │
 Grok         Local TTS         Local STT
              (planned)         (planned)
```

## Supported Providers

### OpenAI Realtime (Current Release)
- **Provider Name:** `openai_realtime`
- **Supports Native Audio:** Yes (built-in TTS and STT)
- **Supports Function Calls:** Yes
- **Audio Format:** 24kHz mono PCM (int16)
- **Configuration:**
  ```ini
  OPENAI_API_KEY=sk-proj-...
  OPENAI_MODEL=gpt-realtime-mini
  ```
- **Description:** Uses OpenAI's Realtime API with built-in bidirectional audio support. Audio streams in real-time without requiring separate TTS/STT services.
- **Best For:** Real-time interactive conversations with immediate audio feedback
- **Feature Parity:** Achieves full feature parity with previous implementation

### Future Providers (In Development)
The following providers are designed but not yet integrated:
- **Grok** - Text-based AI requiring external TTS/STT
- **Claude** - Anthropic's Claude API (text-based)
- **Local TTS/STT** - Offline audio processing using Festival, Vosk, etc.

See `core/providers/_future/` directory for implementations in progress.

## Configuration

### Environment Variables

The OpenAI Realtime provider uses standard environment variables already in your `.env` file:

```bash
# OpenAI API credentials
OPENAI_API_KEY=sk-proj-...

# OpenAI Realtime model (optional)
OPENAI_MODEL=gpt-realtime-mini
```

**No changes required** - If you already have `OPENAI_API_KEY` set, the provider system works out of the box.

### Per-Personality Configuration

In the current release, all personalities use the OpenAI Realtime provider. Future versions will support per-persona provider configuration.

## Usage in Code

### Creating a Provider Instance

```python
from core.providers import OpenAIRealtimeProvider

# Create provider
provider = OpenAIRealtimeProvider()

# Initialize (connect to OpenAI)
await provider.initialize()

# ... use provider ...

# Clean up
await provider.close()
```

### Checking Provider Capabilities

```python
# OpenAI Realtime supports native audio
assert provider.supports_native_audio is True
assert provider.supports_function_calls is True
```

### Sending a Message

```python
from core.providers import AIMessage, MessageRole, ToolDefinition

# Create a message
message = AIMessage(
    role=MessageRole.USER,
    content="Hello, how are you?",
)

# Define tools the AI can call
tools = [
    ToolDefinition(
        name="play_song",
        description="Play a song",
        parameters={
            "type": "object",
            "properties": {
                "song_name": {"type": "string"}
            },
            "required": ["song_name"],
        },
    ),
]

# Stream responses
async for response in provider.send_message(
    message=message,
    conversation_history=[],
    system_prompt="You are Billy, a friendly talking fish",
    tools=tools,
):
    if response.text:
        print(response.text, end="", flush=True)
    if response.audio_bytes:
        output_audio(response.audio_bytes)
    if response.tool_calls:
        for tool in response.tool_calls:
            execute_tool(tool["name"], tool["arguments"])
```

## Error Handling

### Missing OpenAI API Key

Ensure your `.env` file has `OPENAI_API_KEY` set:

```bash
# .env
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
```

If missing, `provider.initialize()` will fail with a connection error.

## Backward Compatibility

This provider system maintains **100% backward compatibility** with the previous implementation:

1. **No configuration changes needed** - Existing `.env` files work unchanged
2. **Same functionality** - OpenAI Realtime API behavior is identical
3. **Same audio format** - 24kHz mono PCM (int16) throughout
4. **Same tools/functions** - All tool definitions work the same way
5. **Same personalities** - Persona configuration unchanged

The provider architecture is purely internal and transparent to the rest of the system.

## Future Extensions

The following providers are designed and ready to integrate (see `core/providers/_future/`):

- **Grok Provider** - Text-based AI with configurable TTS/STT
- **OpenAI TTS Provider** - High-quality text-to-speech synthesis
- **OpenAI STT Provider** - Accurate speech-to-text transcription
- **Local TTS/STT Providers** - Offline audio processing (Festival, Vosk)

## Troubleshooting

### Provider Connection Error
Ensure `OPENAI_API_KEY` is set correctly in `.env` and has valid credentials.

### Feature Parity
The OpenAI Realtime provider achieves 100% feature parity with the previous implementation:
- All tools/functions work identically
- All personality features work identically
- All audio processing works identically
- No breaking changes

## Technical Details

### Message Flow

```
User Speech → OpenAI Realtime API → AI Response → Audio Output
                   ↓
              Function Calls
                   ↓
            Tool Execution
                   ↓
           Function Output
                   ↓
            New AI Response
```

## Performance

- **Latency:** ~100-200ms (network dependent)
- **Real-time:** Yes, bidirectional streaming
- **Audio Format:** 24kHz mono PCM (int16)
- **Optimal:** Wired connection recommended for Raspberry Pi

## Security

- API keys in `.env` - never commit to git
- `.env` is gitignored
- Supports both local and remote deployments
- Future local TTS/STT will enable fully offline operation
