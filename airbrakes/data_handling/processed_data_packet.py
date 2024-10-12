"""Module for describing the data packet for the processed IMU data"""

import msgspec


class ProcessedDataPacket(msgspec.Struct):
    """
    Represents a packet of processed data from the IMU. All of these fields are the processed values of the estimated
    data.
    """

    # pro for processed, I don't like the abbreviation, but it's better consistent est
    proAverageAcceleration: tuple[float, float, float]
    proCurrentAltitude: float
    proSpeedFromAcceleration: float
    proSpeedFromAltitude: float
