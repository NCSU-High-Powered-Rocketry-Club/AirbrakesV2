import threading
import time

import gpiozero
import pytest

from airbrakes.constants import SERVO_DELAY_SECONDS, ServoExtension
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_servo import MockBus, MockServo

approx = pytest.approx
"""
Shortcut for pytest.approx, which is used to compare floating point numbers.
"""


class TestBaseServo:
    """
    Tests the BaseServo class, which controls the servo that extends and retracts the airbrakes.
    """

    def test_slots(self, servo):
        inst = servo
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, servo):
        assert isinstance(servo, MockServo)
        assert isinstance(servo.current_extension, ServoExtension)
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        assert isinstance(servo.servo, MockBus)

    def test_set_extension(self, servo):
        servo.set_max_extension()
        assert servo.current_extension == ServoExtension.MAX_EXTENSION
        servo.set_min_extension()
        assert servo.current_extension == ServoExtension.MIN_EXTENSION

    def test_set_extended(self, servo):
        """
        Tests that the servo extends to the maximum extension, and that threading is handled
        correctly.
        """
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        servo.set_max_extension()
        assert servo.current_extension == ServoExtension.MAX_EXTENSION
        time.sleep(SERVO_DELAY_SECONDS + 0.05)
        assert servo.current_extension == ServoExtension.MAX_EXTENSION

    def test_set_retracted(self, servo):
        """
        Tests that the servo retracts to the minimum extension, and that threading is handled
        correctly.
        """
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        servo.set_min_extension()
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        time.sleep(SERVO_DELAY_SECONDS + 0.05)
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
