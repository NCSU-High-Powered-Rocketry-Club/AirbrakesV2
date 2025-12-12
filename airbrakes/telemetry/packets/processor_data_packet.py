"""
Module for describing the data packet for the processed IMU data.
"""

import msgspec


class ProcessorDataPacket(msgspec.Struct, array_like=True, tag=True):
    """
    Represents a packet of processed data from the IMUDataProcessor.

    All of these fields are the processed values of the IMU's estimated data.
    """

    current_altitude: float
    """
    The zeroed-out altitude of the rocket in meters.

    In other words, the altitude relative to the ground from the launch pad (AGL).
    """

    velocity_magnitude: float
    """
    The magnitude of the rocket's velocity in meters per second.
    """

    vertical_velocity: float
    """
    The vertical velocity of the rocket in meters per second.
    """

    vertical_acceleration: float
    """
    The vertical acceleration of the rocket in meters per second squared.
    """

    current_pitch_degrees: float
    """
    The current pitch of the rocket in degrees.
    """

    time_since_last_data_packet: float
    """
    The time difference between the current and previous data packet in seconds.
    """
