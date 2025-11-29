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

# Global mock instances
mock_gpio_handle = MockGPIOHandle()
mock_button = MockButton(pin=None)


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


def save_motor_log(filepath: str) -> None:
    """Save motor log to a JSON file."""
    import json
    from pathlib import Path

    filepath_obj = Path(filepath)
    filepath_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath_obj, 'w') as f:
        json.dump(get_motor_log(), f, indent=2)


def get_motor_log_pretty() -> str:
    """Get motor log formatted as readable text."""
    with _motor_log_lock:
        if not _motor_log:
            return "No motor events logged"

        lines = ["Motor Event Log:", "=" * 80]
        for event in _motor_log:
            dt = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S.%f")[:-3]
            if event.speed_percent > 0:
                lines.append(
                    f"[{dt}] {event.motor.upper():5} {event.action.upper():10} "
                    f"speed={event.speed_percent:3}% duration={event.duration:.3f}s"
                )
            else:
                lines.append(
                    f"[{dt}] {event.motor.upper():5} {event.action.upper():10} "
                    f"duration={event.duration:.3f}s"
                )
            if event.details:
                for key, value in event.details.items():
                    lines.append(f"        └─ {key}: {value}")

        return "\n".join(lines)


# Virtual button handler support
_virtual_button_handlers: List[Callable] = []


def register_virtual_button_handler(handler: Callable) -> None:
    """Register a handler to be called when virtual button is pressed."""
    _virtual_button_handlers.append(handler)


def trigger_virtual_button() -> None:
    """Simulate a button press (for testing via web UI or CLI)."""
    # Use the mock button's trigger_press() method to properly set is_pressed state
    # This ensures handlers see button.is_pressed=True during execution
    mock_button.trigger_press()


def get_test_status() -> dict:
    """Get current test mode status."""
    status = {
        "test_mode_enabled": _TEST_MODE_ENABLED,
        "motor_events_count": len(get_motor_log()),
        "button_handlers_registered": len(_virtual_button_handlers),
    }

    # Add audio test status if available
    try:
        from . import test_audio
        if _TEST_MODE_ENABLED:
            audio_status = test_audio.get_test_audio_status()
            status["audio"] = audio_status
    except Exception:
        pass

    return status
