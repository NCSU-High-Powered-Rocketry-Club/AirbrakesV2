import pytest

from airbrakes.constants import SERVO_MIN_EXTENSION, SERVO_MAX_EXTENSION
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
        assert servo.servo_extension == SERVO_MAX_EXTENSION

    def test_set_retracted(self, servo):
        """
        Tests that the servo retracts to the minimum extension.
        """
        servo.retract_airbrakes()
        assert servo.servo_extension == SERVO_MIN_EXTENSION

    def test_repeated_extension_retraction(self, servo):
        """
        Tests that repeatedly extending and retracting the servo works as
        expected without crashing.
        """
        servo.extend_airbrakes()
        servo.retract_airbrakes()
        servo.extend_airbrakes()
        servo.retract_airbrakes()

    def test_battery_volts(self, servo):
        """Tests that the mock battery voltage returns a safe default."""
        assert servo.battery_volts == 0.0

    def test_system_current_milliamps(self, servo):
        """Tests that the mock system current returns a safe default."""
        assert servo.system_current_milliamps == 0.0

    def test_servo_voltage(self, servo):
        """Tests that the mock servo voltage returns a safe default."""
        assert servo.servo_voltage == 0.0

    def test_servo_temp(self, servo):
        """Tests that the mock servo temperature returns a safe default."""
        assert servo.servo_temp == 0.0

    def test_get_servo_data_packet(self, servo):
        """Tests that the mock servo data packet returns a safe default."""
        packet = servo.get_servo_data_packet()
        assert packet.current_position == SERVO_MIN_EXTENSION
        assert packet.system_current_milliamps == 0.0
        assert packet.battery_volts == 0.0
        assert packet.voltage == 0.0
        assert packet.current_temp == 0.0