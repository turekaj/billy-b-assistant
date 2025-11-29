"""Unit tests for test_mode module."""

import pytest
from core.test_mode import MockGPIOHandle


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
