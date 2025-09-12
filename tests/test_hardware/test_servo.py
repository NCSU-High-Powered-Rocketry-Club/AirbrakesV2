import threading
import time

import gpiozero
import pytest

from airbrakes.constants import SERVO_DELAY_SECONDS, ServoExtension
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_servo import MockHardwarePWM, MockServo

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
        assert servo.current_extension == ServoExtension.MIN_NO_BUZZ
        assert isinstance(servo.servo, MockHardwarePWM)
        assert servo.servo.hz == 50
        assert isinstance(servo._go_to_max_no_buzz, threading.Timer)
        assert isinstance(servo._go_to_min_no_buzz, threading.Timer)
        assert isinstance(servo.encoder, gpiozero.RotaryEncoder)

    def test_set_extension(self, servo):
        servo._set_extension(ServoExtension.MAX_EXTENSION)
        assert servo.current_extension == ServoExtension.MAX_EXTENSION
        assert servo.servo.duty_cycle == approx(3.33, rel=1e-2)
        servo._set_extension(ServoExtension.MIN_EXTENSION)
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        assert servo.servo.duty_cycle == approx(9.44, rel=1e-2)

    def test_set_extended(self, servo):
        """
        Tests that the servo extends to the maximum extension, and that threading is handled
        correctly.
        """
        assert servo.current_extension == ServoExtension.MIN_NO_BUZZ
        servo.set_extended()
        assert servo.current_extension == ServoExtension.MAX_EXTENSION
        assert servo.servo.duty_cycle == approx(3.33, rel=1e-2)
        time.sleep(SERVO_DELAY_SECONDS + 0.05)
        assert servo.current_extension == ServoExtension.MAX_NO_BUZZ
        assert servo.servo.duty_cycle == approx(3.88, rel=1e-2)

    def test_set_retracted(self, servo):
        """
        Tests that the servo retracts to the minimum extension, and that threading is handled
        correctly.
        """
        assert servo.current_extension == ServoExtension.MIN_NO_BUZZ
        servo.set_retracted()
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        assert servo.servo.duty_cycle == approx(9.44, rel=1e-2)
        time.sleep(SERVO_DELAY_SECONDS + 0.05)
        assert servo.current_extension == ServoExtension.MIN_NO_BUZZ
        assert servo.servo.duty_cycle == approx(8.94, rel=1e-2)

    def test_repeated_extension_retraction(self, servo):
        """
        Tests that repeatedly extending and retracting the servo works as expected, and has no race
        conditions with threads.
        """
        assert servo.current_extension == ServoExtension.MIN_NO_BUZZ

        servo.set_extended()
        assert servo.current_extension == ServoExtension.MAX_EXTENSION
        assert servo.servo.duty_cycle == approx(3.33, rel=1e-2)
        # Assert that going to min no buzz was cancelled:
        assert servo._go_to_min_no_buzz.finished.is_set()
        # Assert that the thread to tell the servo to go to max no buzz has started:
        assert servo._go_to_max_no_buzz._started.is_set()

        time_taken = SERVO_DELAY_SECONDS / 2  # At 0.15s
        time.sleep(time_taken)
        servo.set_retracted()
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        assert servo.servo.duty_cycle == approx(9.44, rel=1e-2)
        # Assert that going to max no buzz was cancelled:
        assert servo._go_to_max_no_buzz.finished.is_set()
        # Assert that the thread to tell the servo to go to min no buzz has started:
        assert servo._go_to_min_no_buzz._started.is_set()

        # At 0.32s, make sure the servo will *not* go to max_no_buzz
        time_taken = SERVO_DELAY_SECONDS / 2 + 0.02  # The 0.02 is to give the code time to execute:
        time.sleep(time_taken)
        assert servo.current_extension == ServoExtension.MIN_EXTENSION
        assert servo.servo.duty_cycle == approx(9.44, rel=1e-2)

        # At 0.45s, make sure the servo will go to min_no_buzz:
        time_taken = SERVO_DELAY_SECONDS / 2
        time.sleep(time_taken)
        assert servo.current_extension == ServoExtension.MIN_NO_BUZZ
        assert servo.servo.duty_cycle == approx(8.94, rel=1e-2)

    def test_encoder_get_position(self, servo):
        """
        Tests that the encoder reading is correct.
        """
        assert servo.get_encoder_reading() == 0
        servo.encoder.steps = 10
        assert servo.get_encoder_reading() == 10
        servo.encoder.steps = -10
        assert servo.get_encoder_reading() == -10
        servo.encoder.steps = 0
        assert servo.get_encoder_reading() == 0

    def test_angle_to_duty_cycle(self):
        """
        Tests that the angle to duty cycle conversion is correct.
        """
        assert Servo._angle_to_duty_cycle(0) == approx(2.5)
        assert Servo._angle_to_duty_cycle(90) == approx(7.5)
        assert Servo._angle_to_duty_cycle(180) == approx(12.5)
        assert Servo._angle_to_duty_cycle(-10) == approx(2.5)  # Test clamping
        assert Servo._angle_to_duty_cycle(190) == approx(12.5)  # Test clamping
