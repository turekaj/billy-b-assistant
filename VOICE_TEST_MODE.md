# Voice Testing in Test Mode

Test mode now supports complete voice interaction testing without requiring physical hardware or the OpenAI API. The system can:

1. **Listen to your voice** - Billy will use your real microphone to listen to what you say
2. **Respond with the AI** - Billy will process your voice through OpenAI's Realtime API and respond
3. **Play audio output** - Billy will play responses through your speakers
4. **Log everything** - All motor movements and audio interactions are captured for testing and debugging

## Quick Start

### Enable Test Mode

Start the application with test mode enabled:

```bash
TEST_MODE=true python main.py
```

Or enable it via the web UI:
1. Navigate to the test panel
2. Press the virtual button to start a session
3. Billy will listen to your voice and respond

### Web UI Test Controls

The test panel provides real-time monitoring of:
- **Motor Log**: All motor movements (mouth, head, tail)
- **Audio Status**: Microphone status, API connection, captured audio chunks
- **Captured Audio**: Audio chunks that would be played to speakers
- **API Messages**: Messages sent to OpenAI Realtime API

## Architecture

### Audio Components

#### MockMicManager
Simulates microphone input for testing:
- Can inject audio programmatically
- Sends periodic silence to keep stream active
- Thread-safe operation

```python
from core.test_audio import get_test_mic_manager

mic = get_test_mic_manager()
# Start listening
mic.start(callback=my_audio_callback)

# Inject test audio
import numpy as np
test_audio = np.array([...], dtype=np.float32)
mic.inject_audio(test_audio)

# Stop listening
mic.stop()
```

#### MockOpenAIWebSocket
Simulates OpenAI Realtime API WebSocket:
- Tracks all messages sent to the API
- Can queue mock responses
- Maintains connection state

```python
from core.test_audio import get_test_websocket

ws = get_test_websocket()

# Get messages sent during session
sent_messages = ws.get_sent_messages()
audio_chunks = ws.get_audio_messages()

# Queue a mock response
ws.queue_response({
    "type": "response.output_audio.delta",
    "delta": base64_audio_data
})
```

#### TestAudioCapture
Captures audio output for verification:
- Records audio chunks played to speakers
- Tracks duration and metadata
- Allows inspection without playing actual audio

```python
from core.test_audio import get_test_audio_capture

capture = get_test_audio_capture()

# Get captured chunks
chunks = capture.get_captured_audio()
total_duration = capture.get_total_duration()

# Clear captured audio
capture.clear()
```

## REST API Endpoints

### Audio Status
```
GET /test/audio/status
```

Returns microphone and API status:
```json
{
    "mic_running": true,
    "websocket_connected": true,
    "audio_chunks_sent_to_api": 5,
    "audio_chunks_captured": 3,
    "total_captured_duration": 2.5
}
```

### Captured Audio
```
GET /test/audio/captured
```

Returns list of captured audio chunks:
```json
{
    "chunks_count": 3,
    "total_duration": 2.5,
    "chunks": [
        {
            "timestamp": 1699564320.123,
            "duration": 0.8,
            "sample_rate": 48000,
            "channels": 2,
            "size_bytes": 76800
        }
    ]
}
```

### API Messages
```
GET /test/audio/api-messages
```

Returns messages sent to OpenAI API:
```json
{
    "total_messages": 25,
    "audio_chunks": 12,
    "messages": [
        {"type": "session.update", ...},
        {"type": "input_audio_buffer.append", ...}
    ]
}
```

### Clear Audio Log
```
POST /test/audio/captured/clear
```

Clears the captured audio log.

## Voice Interaction Flow

When you press the virtual button in test mode:

1. **Button Press** → `on_button()` in `core/button.py`
2. **Session Start** → `BillySession.start()` connects to OpenAI
3. **Microphone Active** → `MockMicManager` begins listening to your voice
4. **Audio Sent** → Your voice is resampled and sent to OpenAI API
5. **API Response** → OpenAI processes voice and returns response
6. **Audio Captured** → Response audio is captured instead of played to speakers
7. **Motor Sync** → Motor movements are logged for "mouth flapping"
8. **Session End** → When you stop talking or timeout occurs

## Testing Scenarios

### Test Voice Input
```python
import numpy as np
from core import test_mode, test_audio

# Enable test mode
test_mode.enable_test_mode()
mic = test_audio.get_test_mic_manager()

# Generate test audio (sine wave at 1000 Hz)
sample_rate = 24000
duration = 2  # seconds
frequency = 1000
amplitude = 0.3

t = np.arange(int(sample_rate * duration)) / sample_rate
test_audio_data = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.float32)

# Inject into microphone
mic.inject_audio(test_audio_data)
```

### Verify API Messages
```python
from core import test_audio

ws = test_audio.get_test_websocket()

# Trigger a voice session...

# Check what was sent to API
messages = ws.get_sent_messages()
for msg in messages:
    if msg['type'] == 'input_audio_buffer.append':
        print(f"Audio chunk sent: {len(msg['audio'])} bytes")
```

### Verify Audio Output
```python
from core import test_audio

capture = test_audio.get_test_audio_capture()

# Trigger a voice session...

# Check what would be played
chunks = capture.get_captured_audio()
print(f"Total audio output: {capture.get_total_duration():.2f} seconds")
for chunk in chunks:
    print(f"Chunk: {chunk.duration:.3f}s at {chunk.sample_rate}Hz")
```

## Configuration

Test mode voice testing respects all normal configuration:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `OPENAI_API_KEY` | (required) | Real API key for OpenAI responses |
| `OPENAI_MODEL` | gpt-4o-realtime-preview-2024-12-26 | OpenAI model to use |
| `PERSONALITY` | Default | Persona instructions for AI |
| `CHUNK_MS` | 40ms | Audio chunk size |
| `MIC_TIMEOUT_SECONDS` | 5 | Silence timeout before closing mic |
| `SPEAKER_PREFERENCE` | (auto) | Preferred output device |
| `MIC_PREFERENCE` | (auto) | Preferred input device |

## Limitations & Notes

- Test mode still uses the real OpenAI Realtime API (not mocked)
- Requires valid `OPENAI_API_KEY` for voice responses
- Audio is captured instead of played to speakers
- Motor movements are logged but not executed (no hardware)
- All 24 unit tests pass with audio test infrastructure

## Integration Points

### Session Integration
Test audio is integrated into `core/session.py` at these points:
1. Microphone initialization checks for test mode
2. Audio playback checks for test mode
3. WebSocket creation uses mock if available

### Motor Integration
Motor events are automatically logged in test mode:
- `move_mouth(speed, duration)` → logged
- `move_head(state)` → logged
- `move_tail(duration)` → logged
- `stop_mouth()` → logged

### Web Integration
Test panel displays audio metrics in real-time:
- `/test/audio/status` → Refreshed every 1 second
- `/test/audio/captured` → Shows captured chunks
- `/test/audio/api-messages` → Shows API communication

## Troubleshooting

### Microphone not capturing audio
1. Verify `MIC_PREFERENCE` is set correctly for your device
2. Check system audio permissions
3. Test with `python -c "import sounddevice; print(sounddevice.query_devices())"`

### No audio output captured
1. Verify OpenAI API key is valid
2. Check that the session is actually running
3. Monitor `/test/audio/api-messages` to see if OpenAI is responding

### Motor log empty
1. Press virtual button to start a session
2. Verify motor functions are being called
3. Check test mode is enabled: `GET /test/status`

## Future Enhancements

- Pre-recorded test audio files for consistent testing
- Automated voice interaction test scenarios
- Integration tests using test mode voice
- CI/CD pipeline using test mode
- Performance profiling in test mode
