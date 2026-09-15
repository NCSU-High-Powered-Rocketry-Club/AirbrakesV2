"""
Module which contains the Servo class, representing a servo motor that
controls the extension of the airbrakes.
"""

import contextlib

with contextlib.suppress(ImportError):
    import gpiod  # ty: ignore[unresolved-import]  # Linux-only optional dependency.

from lewanlib.bus import ServoBus
from lewanlib.servo import Servo as LewanServo

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import (
    BAUDRATE,
    CHIP_PATH,
    I2C_ADDRESS,
    I2C_BUS,
    MAX_EXPECTED_AMPS,
    SERVO_ID,
    SERVO_MIN_EXTENSION,
    SERVO_PORT,
    SERVO_SWITCH_PIN,
    SHUNT_OHMS,
)
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


class Servo(BaseServo):
    """
    A custom class that represents a servo motor.
    The servo controls the extension of airbrakes.

    GPIO switches servo power on the Raspberry Pi 5, while an INA219 sensor
    provides supply and current telemetry.
    """

    __slots__ = (
        "_bus",
        "_ina",
        "_servo",
        "_servo_line",
    )

    def __init__(self) -> None:
        """Initialize GPIO power control, the servo bus, and current sensing."""
        self._servo_line = gpiod.request_lines(
            path=CHIP_PATH,
            consumer="airbrakes-servo",
            config={SERVO_SWITCH_PIN: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT)},
        )

        self._bus = ServoBus(port=SERVO_PORT, baudrate=BAUDRATE, on_exit_power_off=False)
        self._servo = LewanServo(SERVO_ID, self._bus)
        self._servo.move_time_write(SERVO_MIN_EXTENSION, 0)

        from ina219 import INA219  # noqa: PLC0415

        self._ina = INA219(
            shunt_ohms=SHUNT_OHMS,
            address=I2C_ADDRESS,
            max_expected_amps=MAX_EXPECTED_AMPS,
            busnum=I2C_BUS,
        )
        self._ina.configure(
            # sample the current faster (84us per sample instead of 532us per sample with ADC_12BIT,
            # which is the default setting). We lose about ~8mA of resolution.
            shunt_adc=INA219.ADC_9BIT
        )

    @property
    def is_powered(self) -> bool:
        return self._servo.is_powered()

    @property
    def servo_extension(self) -> float:
        return self._servo.pos_read()

    @property
    def battery_volts(self) -> float:
        return self._ina.supply_voltage()

    @property
    def system_current_milliamps(self) -> float:
        return self._ina.current()

    @property
    def servo_voltage(self) -> float:
        return self._servo.vin_read()

    @property
    def servo_temp(self) -> float:
        return self._servo.temp_read()

    def start(self) -> None:
        """Power on the servo and command its minimum extension."""
        self._servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.ACTIVE)
        self._servo.set_powered(True)
        self.retract_airbrakes()

    def stop(self) -> None:
        """Power off the servo and release its GPIO line."""
        self._servo.set_powered(False)
        self._servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.INACTIVE)

        # Release the gpio pin back to the kernel
        self._servo_line.release()

    def extend_airbrakes(self, velocity_meters_per_s: float) -> None:
        extension = self._calculate_deployment_extension(velocity_meters_per_s)
        self.set_extension(self._deployment_extension_to_angle(extension))

    def retract_airbrakes(self) -> None:
        self._servo.move_time_write(SERVO_MIN_EXTENSION, 0)

    def set_extension(self, angle: float) -> None:
        self._servo.move_time_write(angle, 0)

    def get_servo_data_packet(self) -> ServoDataPacket:
        return ServoDataPacket(
            current_position=self.servo_extension,
            system_current_milliamps=self.system_current_milliamps,
            battery_volts=self.battery_volts,
            voltage=self.servo_voltage,
            current_temp=self.servo_temp,
        )
