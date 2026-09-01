"""
Module which contains the Servo class, representing a servo motor that
controls the extension of the airbrakes.
"""

import contextlib


with contextlib.suppress(ImportError):
    import gpiod

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket
from airbrakes.constants import (
    BAUDRATE,
    SERVO_PORT,
    SERVO_ID,
    SERVO_MIN_EXTENSION,
    SERVO_MAX_EXTENSION,
    CHIP_PATH,
    SERVO_SWITCH_PIN,
    SHUNT_OHMS,
    I2C_ADDRESS,
    MAX_EXPECTED_AMPS,
    I2C_BUS,
)

from lewanlib.bus import ServoBus
from lewanlib.servo import Servo as LewanServo

class Servo(BaseServo):
    """
    A custom class that represents a servo motor.
    The servo controls the extension of airbrakes.

    The servo we use is the DS3235, which is a coreless digital servo.
    We only use one servo to control the airbrakes, using hardware PWM
    on the Pi 5.
    """

    __slots__ = (
        "bus",
        "current_extension",
        "ina",
        "servo",
        "servo_line",
    )

    def __init__(self) -> None:
        """
        Initializes the Servo class.
        """
        self.bus = ServoBus(port=SERVO_PORT, baudrate=BAUDRATE, on_exit_power_off=False)
        self.servo = LewanServo(SERVO_ID, self.bus)
        self.servo.move_time_write(SERVO_MIN_EXTENSION, 0)
        self.current_extension: float = SERVO_MIN_EXTENSION

        self.servo_line = gpiod.request_lines(
            path=CHIP_PATH,
            consumer="airbrakes-servo",
            config={SERVO_SWITCH_PIN: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT)},
        )
        
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
        """
        Starts the servo by starting the PWM signal with the initial duty cycle
        corresponding to the minimum extension without buzzing.
        """
        self.servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.ACTIVE)
        self.servo.set_powered(True)
        self.retract_airbrakes()

    def stop(self) -> None:
        """
        Stops the servo by stopping the PWM signal.
        """
        self.servo.set_powered(False)
        self.servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.INACTIVE)

        # Release the gpio pin back to the kernel
        self.servo_line.release()

    def extend_airbrakes(self) -> None:
        """
        Extends the servo to the maximum extension.
        """
        self.servo.move_time_write(SERVO_MAX_EXTENSION, 0)

    def retract_airbrakes(self) -> None:
        """
        Retracts the servo to the minimum extension.
        """
        self.servo.move_time_write(SERVO_MIN_EXTENSION, 0)

    @property
    def servo_extension(self) -> float:
        """
        Gets the extension most recently commanded to the servo.

        :return: The commanded servo extension.
        """
        return self.servo.pos_read()

    @property
    def battery_volts(self) -> float:
        """
        Gets the battery voltage from the INA219 sensor.

        :return: The battery voltage in volts.
        """
        return self.ina.supply_voltage()

    @property
    def system_current_milliamps(self) -> float:
        """
        Gets the current system current draw from the INA219 sensor.

        :return: The current system current draw in milliamps.
        """
        return self.ina.current()

    @property
    def servo_voltage(self) -> float:
        """
        Gets the voltage of the servo motor.

        :return: The servo voltage in volts.
        """
        return self.servo.vin_read()

    @property
    def servo_temp(self) -> float:
        """
        Gets the temperature of the servo motor.

        :return: The servo temperature in degrees Celsius.
        """
        return self.servo.temp_read()

    def get_servo_data_packet(self) -> ServoDataPacket:
        """
        Creates the servo data packet from the servo data.

        :return: The servo data packet.
        """
        return ServoDataPacket(current_position=self.servo_extension,
                               system_current_milliamps=self.system_current_milliamps,
                               battery_volts=self.battery_volts,
                               voltage=self.servo_voltage,
                               current_temp=self.servo_temp)