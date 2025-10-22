"""
Module for the ServoDataPacket class.
"""

import msgspec

from airbrakes.constants import ServoExtension


class ServoDataPacket(msgspec.Struct, tag=True, array_like=True):
    """
    This is a packet of data about the servo.

    It contains the set extension of the servo and the encoder position of the servo.
    """

    set_extension: ServoExtension
    """
    The set extension of the servo.
    """

    encoder_position: int | None
    """
    The position the encoder is currently reading.
    """

    voltage: float
    """
    The voltage being supplied to the servo.
    """

    current: float
    """
    The current being drawn by the servo.
    """
