import pytest

from airbrakes.constants import ServoExtension
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_servo import MockServo

approx = pytest.approx
"""Shortcut for pytest.approx, which is used to compare floating point
numbers."""


class TestBaseServo:
    """
    Tests the BaseServo class, which controls the servo that extends and
    retracts the airbrakes.
    """

    @pytest.fixture
    def servo(self) -> MockServo:
        return MockServo()

    def test_slots(self, servo):
        inst = servo
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, servo):
        assert isinstance(servo, MockServo)

    def test_start(self, servo):
        """
        Tests that start() executes safely.
        """
        servo.start()

    def test_stop(self, servo):
        """
        Tests that stop() executes safely.
        """
        servo.start()
        servo.stop()

    def test_set_extended(self, servo):
        """
        Tests that the servo extends to the maximum extension.
        """
        servo.extend_airbrakes()
        assert servo.servo_extension == ServoExtension.MAX_EXTENSION

    def test_set_retracted(self, servo):
        """
        Tests that the servo retracts to the minimum extension.
        """
        servo.retract_airbrakes()
        assert servo.servo_extension == ServoExtension.MIN_EXTENSION

    def test_repeated_extension_retraction(self, servo):
        """
        Tests that repeatedly extending and retracting the servo works as
        expected without crashing.
        """
        servo.extend_airbrakes()
        servo.retract_airbrakes()
        servo.extend_airbrakes()
        servo.retract_airbrakes()

    def test_angle_to_duty_cycle(self):
        """Tests that the angle to duty cycle conversion is correct."""
        assert Servo._angle_to_duty_cycle(0) == approx(2.5)
        assert Servo._angle_to_duty_cycle(90) == approx(7.5)
        assert Servo._angle_to_duty_cycle(180) == approx(12.5)
        assert Servo._angle_to_duty_cycle(-10) == approx(2.5)  # Test clamping
        assert Servo._angle_to_duty_cycle(190) == approx(12.5)  # Test clamping

    def test_battery_volts(self, servo):
        """Tests that the mock battery voltage returns a safe default."""
        assert servo.battery_volts == 0.0

    def test_system_current_milliamps(self, servo):
        """Tests that the mock system current returns a safe default."""
        assert servo.system_current_milliamps == 0.0

    def test_calculate_deployment_extension(self):
        servo = object.__new__(Servo)

        assert servo._calculate_deployment_extension(0) == approx(1.0)
        assert servo._calculate_deployment_extension(150) == approx(1.0)
        assert servo._calculate_deployment_extension(200) == approx(0.8074, abs=0.001)
        assert servo._calculate_deployment_extension(250) == approx(0.6131, abs=0.001)
        assert servo._calculate_deployment_extension(300) == approx(0.4905, abs=0.001)