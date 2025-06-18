"""
Module for the ServoDataPacket class.
"""

import msgspec


class ServoDataPacket(msgspec.Struct, tag=True, array_like=True):
    """
    This is a packet of data about the servo.

    It contains the set extension of the servo and the encoder position of the servo.
    """

    set_extension: str
    encoder_position: int | None
