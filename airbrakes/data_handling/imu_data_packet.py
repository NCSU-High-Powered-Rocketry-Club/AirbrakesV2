"""Module for describing the data packets from the IMU"""

import msgspec


class IMUDataPacket(msgspec.Struct):
    """
    Base class representing a collection of data packets from the IMU.
    The attributes should be named the same as they are when sent from the IMU -- this just means
    they're going to be in camelCase.
    """

    timestamp: int


class RawDataPacket(IMUDataPacket):
    """
    Represents a raw data packet from the IMU. These values are exactly what the IMU read, without any processing.
    It contains a timestamp and the raw values of the acceleration, gyroscope, and GPS correlation data.
    """

    gpsCorrelTimestampFlags: int | None = None
    gpsCorrelTimestampTow: float | None = None  # Time of week
    gpsCorrelTimestampWeekNum: float | None = None  # Week number
    scaledAccelX: float | None = None
    scaledAccelY: float | None = None
    scaledAccelZ: float | None = None
    scaledGyroX: float | None = None
    scaledGyroY: float | None = None
    scaledGyroZ: float | None = None


class EstimatedDataPacket(IMUDataPacket):
    """
    Represents an estimated data packet from the IMU. These values are the processed values of the
    raw data that are supposed to be more accurate/smoothed. It contains a timestamp and the
    estimated values of the relevant data points.
    """

    estFilterGpsTimeTow: float | None = None  # Time of week
    estFilterGpsTimeWeekNum: int | None = None  # Week number
    estOrientQuaternionX: float | None = None
    estOrientQuaternionY: float | None = None
    estOrientQuaternionZ: float | None = None
    estOrientQuaternionW: float | None = None
    estPressureAlt: float | None = None
    estFilterState: int | None = None
    estFilterDynamicsMode: int | None = None
    estFilterStatusFlags: int | None = None
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
