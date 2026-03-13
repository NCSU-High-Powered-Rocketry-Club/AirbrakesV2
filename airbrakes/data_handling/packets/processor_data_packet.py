"""
Module for describing the data packet for the processed IMU data.
"""

import msgspec


class ProcessorDataPacket(msgspec.Struct, array_like=True, tag=True):
    """
    Represents a packet of processed data from the IMUDataProcessor.

    All of these fields are the processed values of the Firms's estimated data.
    """

    current_altitude: float
    """
    The zeroed-out altitude of the rocket in meters.

    In other words, the altitude relative to the ground from the launch pad (AGL).
    """

    vertical_velocity: float
    """
    The vertical velocity of the rocket in meters per second.
    """

    timestamp_seconds: float
    """
    The timestamp of the packet in seconds.
    """