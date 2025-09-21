"""
Module for describing the data packet for the processed IMU data.
"""

import msgspec


class ProcessorDataPacket(msgspec.Struct, array_like=True, tag=True):
    """
    Represents a packet of processed data from the IMUDataProcessor.

    All of these fields are the processed values of the IMU's estimated data.
    """

    current_timestamp: int
    """
    The timestamp of the data packet in nanoseconds since epoch.
    """

    current_altitude: float
    """
    The zeroed-out altitude of the rocket in meters.

    In other words, the altitude relative to the ground.
    """

    max_altitude: float
    """
    The maximum altitude recorded so far of the rocket in meters.
    """

    vertical_velocity: float
    """
    The vertical velocity of the rocket in meters per second.
    """

    max_vertical_velocity: float
    """
    The maximum vertical velocity recorded so far of the rocket in meters per second.
    """

    average_vertical_acceleration: float
    """
    The average vertical acceleration of the rocket in meters per second squared.
    """

    vertical_acceleration: float
    """
    The vertical acceleration of the rocket in meters per second squared.
    """

    time_since_last_data_packet: float
    """
    The time difference between the current and previous data packet in seconds.
    """
