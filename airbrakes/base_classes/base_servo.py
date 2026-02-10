"""
Base class for the Servo.

This will serve as the base for real servo and the mock servo.
"""

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from LewanLib import ServoDataPacket

class BaseServo(ABC):
    """
    A custom class that represents a servo interface and the accompanying rotary encoder interface.
    The servo controls the extension of the airbrakes while the encoder measures the servo's
    position. The encoder is controlled using the gpiozero library, which provides a simple
    interface for controlling GPIO pins on the Raspberry Pi.

    The servo we use is the DS3235, which is a coreless digital servo. We use hardware PWM to
    control the servo on the Pi 5. We can't use the gpiozero Servo class because it uses software
    PWM, which causes too much jitter (more specifically, the PiGPIO library does not support the Pi
    5, which is why it falls back to software PWM).
    """

    __slots__ = ()

    def __init__(self) -> None:
        """
        Initializes the BaseServo class.
        """

    @abstractmethod
    def set_max_extension(self) -> None:
        """
        Extends the servo to the maximum extension.

        Starts a timer to stop the buzzing after the servo reaches the maximum extension.
        """

    @abstractmethod
    def set_min_extension(self) -> None:
        """
        Retracts the servo to the minimum extension.

        Starts a timer to stop the buzzing after the servo reaches the minimum extension.
        """

    @abstractmethod
    def get_data_packet(self) -> list[ServoDataPacket]:
        """
        Returns all available FIRM data packets from the queued FIRM packets.

        :return: A list containing the latest FIRM data packets from the FIRM packet queue.
        """