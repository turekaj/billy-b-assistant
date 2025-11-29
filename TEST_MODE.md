# Test Mode for Billy B-Assistant

Test mode enables end-to-end testing and development of billy-b-assistant **without requiring Raspberry Pi hardware or GPIO access**. This is useful for:

- Testing the web GUI and API endpoints
- Unit testing motor movements and behaviors
- CI/CD pipelines
- Local development without hardware

## Enabling Test Mode

### Option 1: Environment Variable

Set `TEST_MODE=true` when starting the application:

```bash
TEST_MODE=true python main.py
```

Or in your `.env` file:

```
TEST_MODE=true
```

### Option 2: Programmatically

In your test code:

```python
from core.test_mode import enable_test_mode

enable_test_mode()
```

## Features

### Motor Movement Logging

All motor movements (mouth, head, tail) are logged with timestamps and parameters:

```python
from core import test_mode

test_mode.enable_test_mode()

# Movements are automatically logged
from core.movements import move_mouth
move_mouth(speed_percent=75, duration=0.5)

# View the log
log = test_mode.get_motor_log()
print(test_mode.get_motor_log_pretty())

# Save to JSON
test_mode.save_motor_log("motor_log.json")
```

### Motor Event Data

Each motor event includes:

- **timestamp**: Unix timestamp
- **datetime**: ISO 8601 datetime string
- **motor**: "mouth", "head", or "tail"
- **action**: "on", "off", "async", "brake", "pwm"
- **speed_percent**: 0-100 (0 if not applicable)
- **duration**: Movement duration in seconds
- **details**: Additional metadata (e.g., {"brake": true})

Example log entry:

```json
{
  "timestamp": 1701300123.456,
  "datetime": "2023-11-29T10:35:23.456",
  "motor": "mouth",
  "action": "async",
  "speed_percent": 75,
  "duration": 0.5,
  "details": {"brake": false}
}
```

### Virtual Button

Simulate button presses without physical hardware:

#### Via Web GUI

When test mode is enabled, the web GUI shows a "🧪 Test Mode" panel with:

- **Virtual Button**: Click to simulate a button press
- **Motor Log**: View all motor movements in real-time
- **Motor Log Controls**: Refresh, Clear, Download as JSON

#### Via REST API

```bash
# Trigger virtual button
curl -X POST http://localhost/test/button

# Get test status
curl http://localhost/test/status

# Get motor log
curl http://localhost/test/motor-log

# Clear motor log
curl -X POST http://localhost/test/motor-log/clear

# Download motor log
curl http://localhost/test/motor-log/download > motor_log.json
```

#### Programmatically

```python
from core import test_mode

# Register a handler to run when button is pressed
def on_button_press():
    print("Button pressed!")

test_mode.register_virtual_button_handler(on_button_press)

# Trigger the button
test_mode.trigger_virtual_button()
```

## Using Test Mode in Unit Tests

Test mode integrates seamlessly with pytest:

```python
import pytest
from core import test_mode

@pytest.fixture(autouse=True)
def setup_test_mode():
    test_mode.enable_test_mode()
    test_mode.clear_motor_log()
    yield
    test_mode.clear_motor_log()

def test_head_movement():
    from core.movements import move_head

    # Clear previous logs
    test_mode.clear_motor_log()

    # Perform movement
    move_head("on")

    # Check the log
    log = test_mode.get_motor_log()
    assert len(log) > 0
    assert log[0]["motor"] == "head"
    assert log[0]["action"] == "on"
```

## Test Status API

Get the current test mode status:

```python
status = test_mode.get_test_status()
# Returns:
# {
#     "test_mode_enabled": True,
#     "motor_events_count": 5,
#     "button_handlers_registered": 1
# }
```

## Limitations in Test Mode

- GPIO operations don't actually control hardware (they're mocked)
- Audio playback is not affected by test mode (still uses real audio devices)
- Network operations (MQTT, OpenAI API) still execute normally
- Button input is simulated - physical button still works in real mode

## Example Workflow

```bash
# Terminal 1: Start the application in test mode
TEST_MODE=true python main.py

# Terminal 2: Run tests with pytest
pytest tests/

# In your browser:
# - Open http://localhost
# - View the "🧪 Test Mode" panel
# - Click "Press Virtual Button" to simulate button press
# - Watch motor events appear in the log
# - Download the log for analysis
```

## See Also

- `tests/test_test_mode.py`: Unit tests for test mode functionality
- `core/test_mode.py`: Test mode implementation
- `webconfig/app/routes/test.py`: Test mode REST API endpoints
