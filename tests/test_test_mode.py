"""Unit tests for test_mode module."""

import pytest
import time
from core import test_mode
from core.test_mode import MockGPIOHandle, MockButton, MotorEvent


class TestMockGPIOHandle:
    """Tests for MockGPIOHandle class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.gpio = MockGPIOHandle()

    def test_claim_output(self):
        """Test claiming a GPIO pin."""
        self.gpio.claim_output(22)
        assert 22 in self.gpio.pins
        assert self.gpio.pins[22] == 0

    def test_write(self):
        """Test writing to a GPIO pin."""
        self.gpio.claim_output(22)
        self.gpio.write(22, 1)
        assert self.gpio.pins[22] == 1

    def test_read(self):
        """Test reading from a GPIO pin."""
        self.gpio.claim_output(22)
        self.gpio.write(22, 1)
        assert self.gpio.read(22) == 1

    def test_read_unclaimed_pin(self):
        """Test reading from an unclaimed pin returns 0."""
        assert self.gpio.read(99) == 0

    def test_tx_pwm(self):
        """Test PWM control."""
        self.gpio.claim_output(22)
        self.gpio.tx_pwm(22, 10000, 75)
        assert self.gpio.pwm_state[22]["freq"] == 10000
        assert self.gpio.pwm_state[22]["duty"] == 75

    def test_free(self):
        """Test freeing a GPIO pin."""
        self.gpio.claim_output(22)
        self.gpio.free(22)
        assert 22 not in self.gpio.pins

    def test_close(self):
        """Test closing GPIO handle."""
        self.gpio.claim_output(22)
        self.gpio.claim_output(17)
        self.gpio.close()
        assert len(self.gpio.pins) == 0
        assert len(self.gpio.pwm_state) == 0


class TestMockButton:
    """Tests for MockButton class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.button = MockButton(pin=24, pull_up=True)

    def test_initialization(self):
        """Test button initialization."""
        assert self.button.pin == 24
        assert self.button.pull_up is True
        assert self.button.is_pressed is False

    def test_trigger_press(self):
        """Test triggering button press."""
        pressed_count = {"count": 0}

        def on_press():
            pressed_count["count"] += 1

        self.button.when_pressed = on_press
        self.button.trigger_press()

        assert pressed_count["count"] == 1
        assert self.button.is_pressed is False  # Should reset after trigger

    def test_trigger_press_without_handler(self):
        """Test triggering press without handler doesn't crash."""
        self.button.when_pressed = None
        self.button.trigger_press()  # Should not raise


class TestMotorEvent:
    """Tests for MotorEvent dataclass."""

    def test_motor_event_creation(self):
        """Test creating a motor event."""
        event = MotorEvent(
            timestamp=1000.0,
            motor="mouth",
            action="async",
            speed_percent=75,
            duration=0.5
        )
        assert event.motor == "mouth"
        assert event.action == "async"
        assert event.speed_percent == 75
        assert event.duration == 0.5

    def test_motor_event_to_dict(self):
        """Test converting motor event to dict."""
        event = MotorEvent(
            timestamp=1000.0,
            motor="head",
            action="on",
            speed_percent=80,
            duration=0.0,
            details={"phase": "extend"}
        )
        event_dict = event.to_dict()

        assert event_dict["motor"] == "head"
        assert event_dict["action"] == "on"
        assert event_dict["speed_percent"] == 80
        assert event_dict["duration"] == 0.0
        assert event_dict["details"]["phase"] == "extend"
        assert "datetime" in event_dict


class TestLoggingFunctions:
    """Tests for motor logging functions."""

    def setup_method(self):
        """Reset test mode before each test."""
        test_mode._TEST_MODE_ENABLED = False
        test_mode.clear_motor_log()

    def test_enable_test_mode(self):
        """Test enabling test mode."""
        assert not test_mode.is_test_mode_enabled()
        test_mode.enable_test_mode()
        assert test_mode.is_test_mode_enabled()

    def test_log_motor_event(self):
        """Test logging motor events."""
        test_mode.enable_test_mode()
        test_mode.log_motor_event("mouth", "async", speed_percent=75, duration=0.5)

        log = test_mode.get_motor_log()
        assert len(log) == 1
        assert log[0]["motor"] == "mouth"
        assert log[0]["action"] == "async"
        assert log[0]["speed_percent"] == 75

    def test_log_without_test_mode(self):
        """Test that logging is skipped when test mode is off."""
        test_mode.log_motor_event("mouth", "async")
        log = test_mode.get_motor_log()
        assert len(log) == 0

    def test_clear_motor_log(self):
        """Test clearing motor log."""
        test_mode.enable_test_mode()
        test_mode.log_motor_event("mouth", "async")
        test_mode.log_motor_event("head", "on")

        assert len(test_mode.get_motor_log()) == 2
        test_mode.clear_motor_log()
        assert len(test_mode.get_motor_log()) == 0

    def test_motor_log_timestamps(self):
        """Test that motor events have proper timestamps."""
        test_mode.enable_test_mode()

        before = time.time()
        test_mode.log_motor_event("mouth", "async")
        after = time.time()

        log = test_mode.get_motor_log()
        assert before <= log[0]["timestamp"] <= after

    def test_multiple_motor_events(self):
        """Test logging multiple motor events."""
        test_mode.enable_test_mode()

        test_mode.log_motor_event("mouth", "async", speed_percent=50, duration=0.2)
        test_mode.log_motor_event("head", "on", speed_percent=80, duration=0.5)
        test_mode.log_motor_event("tail", "async", speed_percent=80, duration=0.2)

        log = test_mode.get_motor_log()
        assert len(log) == 3
        assert log[0]["motor"] == "mouth"
        assert log[1]["motor"] == "head"
        assert log[2]["motor"] == "tail"
