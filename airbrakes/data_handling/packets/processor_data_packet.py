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

    vertical_velocity_meters_per_s: float
    """
    The vertical velocity of the rocket in meters per second.
    """

    horizontal_velocity_meters_per_s: float
    """
    The horizontal velocity of the rocket in meters per second.
    """

    tilt_angle_degrees: float
    """
    The total tilt angle of the rocket measured from the +Z axis.
    """

    angular_rate_deg_per_s: float
    """
    The current angular rate of the rocket in degrees per second.
    """

    timestamp_seconds: float
    """
    The timestamp of the packet in seconds.
    """
