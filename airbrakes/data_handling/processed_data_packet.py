"""Module for describing the data packet for the processed IMU data"""

import msgspec


class ProcessedDataPacket(msgspec.Struct):
    """
    Represents a packet of processed data from the IMU. All of these fields are the processed values of the estimated
    data.
    """

    current_altitude: float
    speed: float
    # time_since_last_data_point: float  # dt is the time difference between the current and previous data point
    # gravity_magnitude: float
    # rotated_accels: tuple[float, float, float]
