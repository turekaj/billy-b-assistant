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

### Web GUI Integration
- [ ] Add virtual button to web GUI (`webconfig/templates/components/test-panel.html`)
- [ ] Add test mode REST API endpoints (`webconfig/app/routes/test.py`)
- [ ] Register test routes in Flask app (`webconfig/app/__init__.py`)
- [ ] Display motor log in real-time on web UI
- [ ] Add controls to refresh, clear, and download motor logs

### Backend Integration
- [ ] Update `core/button.py` to use test_mode in `start_loop()`
  - Register virtual button handler
  - Display test mode status in logs

- [ ] Update `core/movements.py` motor functions to log events
  - Add logging to `move_mouth()`, `move_head()`, `move_tail()`
  - Add logging to all motor control functions
  - Pass motor name and action details

- [ ] Update `main.py` to support TEST_MODE environment variable
  - Check for TEST_MODE=true on startup
  - Call `enable_test_mode()` if set

- [ ] Complete remaining GPIO operation overrides in `movements.py`
  - Update all `lgpio` calls to use `_get_gpio_handle()`
  - Handle test mode in all GPIO functions
  - Ensure mock GPIO handle is used in test mode

### Future Enhancements
- [ ] Motor movement simulation in test mode (replay recorded movements)
- [ ] Audio simulation mode (mock sounddevice for testing without audio)
- [ ] WebSocket simulation for OpenAI Realtime API testing
- [ ] Integration tests using test mode
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
- [ ] Integration tests for movements with test mode logging
- [ ] Web GUI tests for virtual button functionality
- [ ] API endpoint tests for motor log retrieval
- [ ] End-to-end test simulation with button press
- [ ] Performance tests in test mode

## Git Branches

- `feature/test-mode` - Main feature branch with 9 atomic commits:
  1. MockGPIOHandle class with tests
  2. MockButton class with tests
  3. MotorEvent dataclass with tests
  4. Motor logging functions with tests
  5. Helper functions and virtual button support with tests
  6. Lazy GPIO initialization
  7. TEST_MODE.md documentation
  8. Make GPIO optional, add pytest
  9. Build-system configuration

Ready for: Code review → PR → Merge to main
