"""
Module which contains the Servo class, representing a servo motor that controls the extension of the
airbrakes, along with a rotary encoder to measure the servo's position.
"""

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import (
    ServoExtension,
    SERVO_EXTENSION_TIME,
    SERVO_ID
)

if TYPE_CHECKING:
    from LewanLib import Servo, ServoDataPacket
    from airbrakes.mock.mock_servo import MockServo


class Servo(BaseServo):
    """
    A custom class that represents a servo motor and the accompanying rotary encoder. The servo
    controls the extension of the airbrakes while the encoder measures the servo's position. the
    encoder is controlled using the gpiozero library, which provides a simple interface for
    controlling GPIO pins on the Raspberry Pi 5.

    The servo we use is the DS3235, which is a coreless digital servo. We only use one servo to
    control the airbrakes, using hardware PWM on the Pi 5.
    """

    __slots__ = (
        "servo",
    )

    def __init__(self) -> None:
        """
        Initializes the Servo class.

        """
        super().__init__()

        self.servo = Servo(SERVO_ID)
        self.servo.move_time_write(ServoExtension.MIN_EXTENSION, SERVO_EXTENSION_TIME)


    def set_max_extension(self, extension: ServoExtension) -> None:
        """
        Sets the servo to the specified extension.

        :param extension: The extension to set the servo to.
        """
        # If we are already going to the minimum extension, we cancel that operation before
        # extending the servo.
        self.servo.move_time_write((ServoExtension.MAX_EXTENSION), SERVO_EXTENSION_TIME)

    def set_min_extension(self, extension: ServoExtension) -> None:
        """
        Retracts the servo to the minimum extension.
        """

        self.servo.move_time_write((ServoExtension.MIN_EXTENSION), SERVO_EXTENSION_TIME)


    def get_data_packet(self) -> list[ServoDataPacket]:
        return self.servo.get_data_packets()