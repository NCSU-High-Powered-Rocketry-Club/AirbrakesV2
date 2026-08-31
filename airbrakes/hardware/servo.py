"""
Module which contains the Servo class, representing a servo motor that
controls the extension of the airbrakes.
"""

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import (
    BAUDRATE,
    SERVO_PORT,
    SERVO_ID,
    ServoExtension,
)

from lewanlib.bus import ServoBus
from lewanlib.servo import Servo as LewanServo
from lewanlib.servo_data_packet import ServoDataPacket


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
        self.servo.move_time_write(ServoExtension.MIN_EXTENSION.value, 0)
        self.current_extension: ServoExtension = ServoExtension.MIN_EXTENSION

    def start(self) -> None:
        """
        Starts the servo by starting the PWM signal with the initial duty cycle
        corresponding to the minimum extension without buzzing.
        """
        # Switch on the servo switch
        pass

    def stop(self) -> None:
        """
        Stops the servo by stopping the PWM signal.
        """
        pass

    def extend_airbrakes(self) -> None:
        """
        Extends the servo to the maximum extension.
        """
        self.servo.move_time_write(ServoExtension.MAX_EXTENSION.value, 0)

    def retract_airbrakes(self) -> None:
        """
        Retracts the servo to the minimum extension.
        """
        self.servo.move_time_write(ServoExtension.MIN_EXTENSION.value, 0)

    @property
    def servo_extension(self) -> ServoExtension:
        """
        Gets the extension most recently commanded to the servo.

        :return: The commanded servo extension.
        """
        return ServoExtension(round(self.servo.pos_read()))

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
        Gets the servo data packet from the servo.

        :return: The servo data packet.
        """
        return self.servo.return_data_packet()