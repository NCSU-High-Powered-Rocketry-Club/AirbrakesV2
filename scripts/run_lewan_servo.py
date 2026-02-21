"""Unit tests for bus module."""

import pytest
from lewanlib import constants
from lewanlib.bus import ServoBus
import time

def test_move_time_write():
    """Test writing move time parameters to servo."""
    port = "/dev/ttyAMA0"

    with ServoBus(port=port, baudrate=115200) as bus:
        servo = bus.get_servo(1)
        start = time.time()
        servo.move_time_write(constants.MAX_ANGLE_DEGREES, 2, wait=True) 
        assert time.time() - start == 2, \
            f"Move time should be 2 seconds, got {time.time() - start} seconds"
        assert servo.pos_read() == constants.MAX_ANGLE_DEGREES, \
            f"Servo should be at {constants.MAX_ANGLE_DEGREES}°, got {servo.pos_read()}°"

def test_move_time_read():
    """Test reading move time parameters from servo."""
    port = "/dev/ttyAMA0"

    with ServoBus(port=port, baudrate=115200) as bus:
        servo = bus.get_servo(1)
        servo.move_time_write(constants.MIN_ANGLE_DEGREES, 1)
        angle, time_s = servo.move_time_read()
        assert angle == constants.MIN_ANGLE_DEGREES, f"Move time read angle should be {constants.MIN_ANGLE_DEGREES}°, got {angle}°"
        assert time_s == 1, f"Move time read time should be 1 second, got {time_s} seconds"

def test_angle_offset_methods():
    """Test angle offset adjustment, writing, and reading methods."""
    # Mock the serial connection to avoid hardware dependencies
    port = "/dev/ttyAMA0"

    # Create a ServoBus instance with the mock
    with ServoBus(port=port, baudrate=115200) as bus:
        servo = bus.get_servo(1)
        servo.angle_offset_adjust(1, 15.0, write=False)
        assert servo.angle_offset_read() == 15.0, \
            f"Angle offset should be 15.0°, got {servo.angle_offset_read()}°"
