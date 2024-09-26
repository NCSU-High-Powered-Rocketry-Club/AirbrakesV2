"""Module for describing the data packet for the logger to log"""

import msgspec

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket


class LoggedDataPacket(msgspec.Struct):
    """
    Represents a collection of all data that the logger can log in a line. Not every field will be filled in every
    packet. While maybe not the sleekest solution, it is very easy to implement, and allows us to see exactly what data
    we are logging.
    """

    state: str
    extension: float

    # Raw Data Packet Fields
    scaledAccelX: float | None = None
    scaledAccelY: float | None = None
    scaledAccelZ: float | None = None
    scaledGyroX: float | None = None
    scaledGyroY: float | None = None
    scaledGyroZ: float | None = None

    # Estimated Data Packet Fields
    stOrientQuaternionX: float | None = None
    estOrientQuaternionY: float | None = None
    estOrientQuaternionZ: float | None = None
    estOrientQuaternionW: float | None = None
    estPressureAlt: float | None = None
    estAttitudeUncertQuaternionX: float | None = None
    estAttitudeUncertQuaternionY: float | None = None
    estAttitudeUncertQuaternionZ: float | None = None
    estAttitudeUncertQuaternionW: float | None = None
    estAngularRateX: float | None = None
    estAngularRateY: float | None = None
    estAngularRateZ: float | None = None
    estCompensatedAccelX: float | None = None
    estCompensatedAccelY: float | None = None
    estCompensatedAccelZ: float | None = None
    estLinearAccelX: float | None = None
    estLinearAccelY: float | None = None
    estLinearAccelZ: float | None = None

    # Processed Data Packet Fields
    avg_acceleration: tuple[float, float, float]
    avg_acceleration_mag: float
    current_altitude: float
    speed: float
    # Not logging maxes because they are easily found
