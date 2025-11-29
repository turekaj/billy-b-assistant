"""Test mode support for billy-b-assistant - GPU mocking."""

from typing import Dict, Callable, Optional


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
