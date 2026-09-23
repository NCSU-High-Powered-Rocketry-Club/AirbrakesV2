import sys
from types import SimpleNamespace

import pytest

import airbrakes.hardware.servo as servo_module
from airbrakes.constants import (
    BAUDRATE,
    I2C_ADDRESS,
    I2C_BUS,
    MAX_EXPECTED_AMPS,
    SERVO_ID,
    SERVO_MAX_EXTENSION,
    SERVO_MIN_EXTENSION,
    SERVO_PORT,
    SHUNT_OHMS,
)
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
        servo.extend_airbrakes(0.0)
        assert servo.servo_extension == SERVO_MAX_EXTENSION

    def test_set_retracted(self, servo):
        """
        Tests that the servo retracts to the minimum extension.
        """
        servo.retract_airbrakes()
        assert servo.servo_extension == SERVO_MIN_EXTENSION

    def test_set_extension(self, servo):
        """
        Tests that the servo can be set to a specific extension.
        """
        test_extension = (SERVO_MAX_EXTENSION + SERVO_MIN_EXTENSION) / 2
        servo.set_extension(test_extension)
        assert servo.servo_extension == test_extension

    def test_repeated_extension_retraction(self, servo):
        """
        Tests that repeatedly extending and retracting the servo works as
        expected without crashing.
        """
        servo.extend_airbrakes(0.0)
        servo.retract_airbrakes()
        servo.extend_airbrakes(0.0)
        servo.retract_airbrakes()

    def test_extend_airbrakes_cancels_existing(self, monkeypatch, servo):
        class MockTimer:
            def __init__(self, _, callback, args):
                self.callback = callback
                self.args = args
                self.cancelled = False

            def start(self):
                pass

            def cancel(self):
                self.cancelled = True

            def fire(self):
                if not self.cancelled:
                    self.callback(*self.args)

        monkeypatch.setattr("airbrakes.mock.mock_servo.threading.Timer", MockTimer)

        servo.extend_airbrakes(0.0)
        first_timer = servo.extend
        servo.extend_airbrakes(300.0)
        second_timer = servo.extend

        assert first_timer is not None
        assert second_timer is not None
        assert first_timer.cancelled
        assert not second_timer.cancelled
        first_timer.fire()

    def test_battery_volts(self, servo):
        """Tests that the mock battery voltage returns a safe default."""
        assert servo.battery_volts == 0.0

    def test_system_current_milliamps(self, servo):
        """Tests that the mock system current returns a safe default."""
        assert servo.system_current_milliamps == 0.0

    def test_calculate_deployment_extension(self):
        servo = MockServo()

        assert servo._calculate_deployment_extension(0) == approx(1.0)
        # All of these values were calculated using the _calculate_deployment_extension method,
        # so if any constants in that change these will as well.
        assert servo._calculate_deployment_extension(150) == approx(1.0, abs=0.001)
        assert servo._calculate_deployment_extension(200) == approx(0.6264, abs=0.001)
        assert servo._calculate_deployment_extension(250) == approx(0.3581, abs=0.001)
        assert servo._calculate_deployment_extension(300) == approx(0.252, abs=0.001)
        assert servo._calculate_deployment_extension(350) == approx(0.194, abs=0.001)
        assert servo._calculate_deployment_extension(float("nan")) == 0.0

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


class TestServo:
    """Tests the real Servo implementation with its hardware dependencies mocked."""

    @pytest.fixture
    def servo(self, monkeypatch) -> Servo:
        class MockLine:
            def __init__(self) -> None:
                self.values: list[tuple[int, object]] = []
                self.released = False

            def set_value(self, pin: int, value: object) -> None:
                self.values.append((pin, value))

            def release(self) -> None:
                self.released = True

        class MockGpiod:
            class line:
                class Direction:
                    OUTPUT = object()

                class Value:
                    ACTIVE = object()
                    INACTIVE = object()

            class LineSettings:
                def __init__(self, direction: object) -> None:
                    self.direction = direction

            line_request: MockLine | None = None

            @classmethod
            def request_lines(cls, **_: object) -> MockLine:
                cls.line_request = MockLine()
                return cls.line_request

        class MockServoBus:
            def __init__(self, port: str, baudrate: int, on_exit_power_off: bool) -> None:
                self.port = port
                self.baudrate = baudrate
                self.on_exit_power_off = on_exit_power_off

        class MockLewanServo:
            def __init__(self, servo_id: int, bus: MockServoBus) -> None:
                self.servo_id = servo_id
                self.bus = bus
                self.moves: list[tuple[float, int]] = []
                self.powered = False

            def move_time_write(self, angle: float, time: int) -> None:
                self.moves.append((angle, time))

            def set_powered(self, powered: bool) -> None:
                self.powered = powered

            def is_powered(self) -> bool:
                return self.powered

            def pos_read(self) -> float:
                return 42.0

            def vin_read(self) -> float:
                return 7.4

            def temp_read(self) -> float:
                return 25.0

        class MockINA219:
            ADC_9BIT = object()

            def __init__(
                self,
                shunt_ohms: float,
                address: int,
                max_expected_amps: float,
                busnum: int,
            ) -> None:
                self.shunt_ohms = shunt_ohms
                self.address = address
                self.max_expected_amps = max_expected_amps
                self.busnum = busnum
                self.configured_with: object | None = None

            def configure(self, shunt_adc: object) -> None:
                self.configured_with = shunt_adc

            def supply_voltage(self) -> float:
                return 12.1

            def current(self) -> float:
                return 350.0

        monkeypatch.setattr(servo_module, "gpiod", MockGpiod, raising=False)
        monkeypatch.setattr(servo_module, "ServoBus", MockServoBus)
        monkeypatch.setattr(servo_module, "LewanServo", MockLewanServo)
        monkeypatch.setitem(sys.modules, "ina219", SimpleNamespace(INA219=MockINA219))
        return Servo()

    def test_operations(self, servo: Servo) -> None:
        assert servo.__slots__ == ("_bus", "_ina", "_servo", "_servo_line")
        assert not hasattr(servo, "bus")
        assert not hasattr(servo, "ina")
        assert not hasattr(servo, "servo")
        assert not hasattr(servo, "servo_line")

        assert servo._bus.port == SERVO_PORT
        assert servo._bus.baudrate == BAUDRATE
        assert servo._bus.on_exit_power_off is False
        assert servo._servo.servo_id == SERVO_ID
        assert servo._servo.bus is servo._bus
        assert servo._servo.moves == [(SERVO_MIN_EXTENSION, 0)]
        assert servo._ina.shunt_ohms == SHUNT_OHMS
        assert servo._ina.address == I2C_ADDRESS
        assert servo._ina.max_expected_amps == MAX_EXPECTED_AMPS
        assert servo._ina.busnum == I2C_BUS
        assert servo._ina.configured_with is servo._ina.ADC_9BIT

        servo.start()
        servo.extend_airbrakes(0.0)
        servo.set_extension(45.0)

        assert servo.is_powered
        assert servo._servo.moves == [
            (SERVO_MIN_EXTENSION, 0),
            (SERVO_MIN_EXTENSION, 0),
            (SERVO_MAX_EXTENSION, 0),
            (45.0, 0),
        ]
        assert servo.servo_extension == 42.0
        assert servo.battery_volts == 12.1
        assert servo.system_current_milliamps == 350.0
        assert servo.servo_voltage == 7.4
        assert servo.servo_temp == 25.0

        packet = servo.get_servo_data_packet()
        assert packet.current_position == 42.0
        assert packet.system_current_milliamps == 350.0
        assert packet.battery_volts == 12.1
        assert packet.voltage == 7.4
        assert packet.current_temp == 25.0

        servo.stop()
        assert not servo.is_powered
        assert servo._servo_line.released

    def test_extend_airbrakes_uses_the_force_limited_extension(self, servo: Servo) -> None:
        servo.extend_airbrakes(300.0)
        # This was just calculated using the _calculate_deployment_extension method,
        # and is the expected extension for a velocity of 300.0
        assert servo._servo.moves[-1] == approx((45.365, 0), abs=0.01)
