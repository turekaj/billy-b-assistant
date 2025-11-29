"""Test mode support for billy-b-assistant - GPU mocking."""

import time
import threading
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


class MockGPIOHandle:
    """Mock GPIO chip handle that simulates lgpio interface."""

    def __init__(self):
        self.pins: Dict[int, int] = {}
        self.pwm_state: Dict[int, Dict] = {}

    def claim_output(self, pin: int) -> None:
        """Mock gpio_claim_output."""
        if pin not in self.pins:
            self.pins[pin] = 0
            self.pwm_state[pin] = {"duty": 0, "freq": 0}

    def write(self, pin: int, value: int) -> None:
        """Mock gpio_write."""
        if pin in self.pins:
            self.pins[pin] = value

    def read(self, pin: int) -> int:
        """Mock gpio_read."""
        return self.pins.get(pin, 0)

    def tx_pwm(self, pin: int, freq: int, duty: int) -> None:
        """Mock tx_pwm."""
        if pin in self.pins:
            self.pwm_state[pin] = {"freq": freq, "duty": duty}

    def free(self, pin: int) -> None:
        """Mock gpio_free."""
        if pin in self.pins:
            del self.pins[pin]

    def close(self) -> None:
        """Mock gpiochip_close."""
        self.pins.clear()
        self.pwm_state.clear()


class MockButton:
    """Mock button that simulates gpiozero Button interface."""

    def __init__(self, pin: int, pull_up: bool = True):
        self.pin = pin
        self.pull_up = pull_up
        self.is_pressed = False
        self.when_pressed: Optional[Callable] = None

    def trigger_press(self) -> None:
        """Simulate button press (for testing)."""
        self.is_pressed = True
        if self.when_pressed:
            self.when_pressed()
        self.is_pressed = False


@dataclass
class MotorEvent:
    """Record of a motor movement event."""
    timestamp: float
    motor: str  # "mouth", "head", "tail"
    action: str  # "on", "off", "brake", "pwm", "async"
    speed_percent: int = 0
    duration: float = 0.0
    details: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "motor": self.motor,
            "action": self.action,
            "speed_percent": self.speed_percent,
            "duration": self.duration,
            "details": self.details,
        }


# Global test mode state
_TEST_MODE_ENABLED = False
_motor_log: List[MotorEvent] = []
_motor_log_lock = threading.Lock()


def enable_test_mode() -> None:
    """Enable test mode, disabling GPIO hardware access."""
    global _TEST_MODE_ENABLED
    _TEST_MODE_ENABLED = True


def is_test_mode_enabled() -> bool:
    """Check if test mode is currently enabled."""
    return _TEST_MODE_ENABLED


def log_motor_event(motor: str, action: str, speed_percent: int = 0,
                   duration: float = 0.0, details: dict = None) -> None:
    """Log a motor movement event."""
    if not _TEST_MODE_ENABLED:
        return

    event = MotorEvent(
        timestamp=time.time(),
        motor=motor,
        action=action,
        speed_percent=speed_percent,
        duration=duration,
        details=details or {}
    )

    with _motor_log_lock:
        _motor_log.append(event)


def get_motor_log() -> List[dict]:
    """Get all logged motor events as dicts."""
    with _motor_log_lock:
        return [event.to_dict() for event in _motor_log]


def clear_motor_log() -> None:
    """Clear all logged motor events."""
    global _motor_log
    with _motor_log_lock:
        _motor_log.clear()
