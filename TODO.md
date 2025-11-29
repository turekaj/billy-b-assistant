# TODO - Billy B-Assistant Test Mode

## Completed ✅

- [x] Create test mode abstraction layer (`core/test_mode.py`)
  - MockGPIOHandle class
  - MockButton class
  - MotorEvent dataclass
  - Motor logging functions
  - Virtual button support
  - Helper functions (pretty printing, file saving, status reporting)

- [x] Create comprehensive unit tests
  - 24 tests covering all test_mode functionality
  - All tests passing

- [x] Make GPIO libraries optional
  - gpiozero and lgpio are now optional dependencies
  - Graceful error messages when not installed
  - Installation options: `.[rpi]`, `.[test]`, `.[dev]`

- [x] Add pytest to test dependencies
  - pytest configured in pyproject.toml
  - Can run tests with `python -m pytest tests/`

- [x] Document test mode usage
  - TEST_MODE.md with comprehensive examples
  - Usage guide for web GUI, REST API, and programmatic access

- [x] Lazy GPIO initialization
  - GPIO only initialized when first needed
  - Allows test mode to work without hardware
  - Graceful error handling for missing libraries

## In Progress 🔄

None currently - all core test mode functionality complete!

## Remaining Features (Optional) 📋

### Web GUI Integration ✅
- [x] Add virtual button to web GUI (`webconfig/templates/components/test-panel.html`)
- [x] Add test mode REST API endpoints (`webconfig/app/routes/test.py`)
- [x] Register test routes in Flask app (`webconfig/app/__init__.py`)
- [x] Display motor log in real-time on web UI
- [x] Add controls to refresh, clear, and download motor logs
- [x] Include test panel in main index page

### Backend Integration ✅
- [x] Update `core/button.py` to use test_mode in `start_loop()`
  - Register virtual button handler
  - Display test mode status in logs

- [x] Update `core/movements.py` motor functions to log events
  - Add logging to `move_mouth()`, `move_head()`, `move_tail()`
  - Add logging to all motor control functions
  - Pass motor name and action details

- [x] Update `main.py` to support TEST_MODE environment variable
  - Check for TEST_MODE=true on startup
  - Call `enable_test_mode()` if set

- [x] Complete remaining GPIO operation overrides in `movements.py`
  - Update all `lgpio` calls to use `_get_gpio_handle()`
  - Handle test mode in all GPIO functions
  - Ensure mock GPIO handle is used in test mode

### Audio Voice Testing Features ✅
- [x] Mock microphone input (`test_audio.MockMicManager`)
  - Simulates microphone input without hardware
  - Can inject test audio programmatically

- [x] Mock OpenAI Realtime API WebSocket (`test_audio.MockOpenAIWebSocket`)
  - Simulates OpenAI API responses
  - Configurable response delays
  - Tracks all messages sent to API

- [x] Audio capture system (`test_audio.TestAudioCapture`)
  - Captures audio chunks that would be played to speakers
  - Allows verification of what would be output
  - Tracks duration and metadata

- [x] Web UI for audio testing
  - Real-time audio status display
  - Captured audio chunk monitoring
  - API message inspection

- [x] REST API endpoints for audio testing
  - `/test/audio/status` - Microphone and API status
  - `/test/audio/captured` - List captured audio chunks
  - `/test/audio/api-messages` - Messages sent to OpenAI
  - `/test/audio/captured/clear` - Clear captured audio log

### Future Enhancements
- [ ] Pre-recorded test audio files for voice testing
- [ ] Automated voice interaction test scenarios
- [ ] Motor movement simulation in test mode (replay recorded movements)
- [ ] Integration tests using test mode voice scenarios
- [ ] CI/CD pipeline using test mode
- [ ] Performance profiling in test mode

## Notes

- All test mode code is backward compatible - doesn't affect normal RPi operation
- Tests can run on any machine without Raspberry Pi hardware
- Environment variable `TEST_MODE=true` enables test mode
- Motor events are logged with precise timestamps for analysis
- Virtual button allows simulating user interaction in tests

## Testing Checklist

- [x] Unit tests for test_mode module (24/24 passing)
- [x] Motor function test_mode logging (implemented and tested)
- [x] Button handler registration in test mode (implemented)
- [x] TEST_MODE environment variable support (implemented)
- [x] GPIO operation overrides for test mode (implemented)
- [x] Web GUI test panel with motor log display (implemented)
- [x] REST API endpoints for test mode control (implemented)
- [ ] Integration tests for end-to-end test scenario
- [ ] Manual testing with TEST_MODE=true environment variable

## Git Branches

- `feature/test-mode` - Main feature branch with complete implementation:
  1. MockGPIOHandle class with tests ✅
  2. MockButton class with tests ✅
  3. MotorEvent dataclass with tests ✅
  4. Motor logging functions with tests ✅
  5. Helper functions and virtual button support with tests ✅
  6. Lazy GPIO initialization ✅
  7. TEST_MODE.md documentation ✅
  8. Make GPIO optional, add pytest ✅
  9. Build-system configuration ✅
  10. Backend integration (motor logging, button handlers, TEST_MODE env var) ✅
  11. Web GUI test panel and API endpoints ✅
  12. GPIO operation overrides for test mode ✅

**Implementation Status: COMPLETE ✅**

All core and optional features implemented. All 24 unit tests passing.
Ready for: Testing → Code review → PR → Merge to main
