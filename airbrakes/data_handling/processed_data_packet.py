"""Module for describing the data packet for the processed IMU data"""

import msgspec


class ProcessedDataPacket(msgspec.Struct):
    """
    Represents a packet of processed data from the IMU. All of these fields are the processed values of the estimated
    data.
    """

    avg_acceleration: tuple[float, float, float]
    avg_acceleration_mag: float
    max_altitude: float
    current_altitude: float
    speed: float
    max_speed: float