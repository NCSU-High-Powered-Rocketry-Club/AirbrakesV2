"""
Module which contains the Servo class, representing a servo motor that
controls the extension of the airbrakes.
"""

import contextlib

with contextlib.suppress(ImportError):
    import gpiod

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
    SERVO_MAX_EXTENSION,
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
        "bus",
        "ina",
        "servo",
        "servo_line",
    )

    def __init__(self) -> None:
        """Initialize GPIO power control, the servo bus, and current sensing."""
        self.servo_line = gpiod.request_lines(
            path=CHIP_PATH,
            consumer="airbrakes-servo",
            config={SERVO_SWITCH_PIN: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT)},
        )

        self.bus = ServoBus(port=SERVO_PORT, baudrate=BAUDRATE, on_exit_power_off=False)
        self.servo = LewanServo(SERVO_ID, self.bus)
        self.servo.move_time_write(SERVO_MIN_EXTENSION, 0)

        from ina219 import INA219  # noqa: PLC0415

        self.ina = INA219(
            shunt_ohms=SHUNT_OHMS,
            address=I2C_ADDRESS,
            max_expected_amps=MAX_EXPECTED_AMPS,
            busnum=I2C_BUS,
        )
        self.ina.configure(
            # sample the current faster (84us per sample instead of 532us per sample with ADC_12BIT,
            # which is the default setting). We lose about ~8mA of resolution.
            shunt_adc=INA219.ADC_9BIT
        )

    def start(self) -> None:
        """Power on the servo and command its minimum extension."""
        self.servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.ACTIVE)
        self.servo.set_powered(True)
        self.retract_airbrakes()

    def stop(self) -> None:
        """Power off the servo and release its GPIO line."""
        self.servo.set_powered(False)
        self.servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.INACTIVE)

        # Release the gpio pin back to the kernel
        self.servo_line.release()

    def extend_airbrakes(self) -> None:
        """Command the physical servo to its maximum extension."""
        self.servo.move_time_write(SERVO_MAX_EXTENSION, 0)

    def retract_airbrakes(self) -> None:
        """Command the physical servo to its minimum extension."""
        self.servo.move_time_write(SERVO_MIN_EXTENSION, 0)

    def set_extension(self, angle: float) -> None:
        """
        Command a specific servo position.

        :param angle: The desired servo position in degrees.
        """
        self.servo.move_time_write(angle, 0)

    @property
    def is_powered(self) -> bool:
        """Return whether the physical servo reports that it is powered."""
        return self.servo.is_powered()

    @property
    def servo_extension(self) -> float:
        """Return the physical servo position reported by the Lewan bus."""
        return self.servo.pos_read()

    @property
    def battery_volts(self) -> float:
        """Return the battery voltage measured by the INA219 sensor."""
        return self.ina.supply_voltage()

    @property
    def system_current_milliamps(self) -> float:
        """Return the system current measured by the INA219 sensor."""
        return self.ina.current()

    @property
    def servo_voltage(self) -> float:
        """Return the servo motor voltage reported by the Lewan bus."""
        return self.servo.vin_read()

    @property
    def servo_temp(self) -> float:
        """Return the servo temperature reported by the Lewan bus."""
        return self.servo.temp_read()

    def get_servo_data_packet(self) -> ServoDataPacket:
        """Create a data packet from the physical servo's telemetry."""
        return ServoDataPacket(
            current_position=self.servo_extension,
            system_current_milliamps=self.system_current_milliamps,
            battery_volts=self.battery_volts,
            voltage=self.servo_voltage,
            current_temp=self.servo_temp,
        )
