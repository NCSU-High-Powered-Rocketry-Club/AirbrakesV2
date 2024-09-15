"""Module for describing the datapackets from the IMU"""


def _mro_slots(obj) -> list[str]:
    """Helper function to get all __slots__ from the MRO (Method Resolution Order) of an object"""
    return [
        attr
        for cls in obj.__class__.__mro__[:-1]  # :-1 doesn't include the object class
        for attr in cls.__slots__
    ]


class IMUDataPacket:
    """
    Base class representing a collection of data packets from the IMU.
    The attributes should be named the same as they are when sent from the IMU -- this just means
    they're going to be in camelCase.

    Args:
        timestamp (int): The timestamp of the data packet in nanoseconds.
    """

    __slots__ = ("timestamp",)

    def __init__(self, timestamp: int):
        self.timestamp = timestamp

    def __str__(self):
        attributes = ", ".join(f"{attr}={getattr(self, attr)}" for attr in _mro_slots(self))
        return f"{self.__class__.__name__}({attributes})"


class RawDataPacket(IMUDataPacket):
    """
    Represents a raw data packet from the IMU. These values are exactly what the IMU read, without any processing.
    It contains a timestamp and the raw values of the acceleration, gyroscope, and GPS correlation data.
    """

    __slots__ = (
        "gpsCorrelTimestampFlags",
        "gpsCorrelTimestampTow",  # Time of week
        "gpsCorrelTimestampWeekNum",  # Week number
        "scaledAccelX",
        "scaledAccelY",
        "scaledAccelZ",
        "scaledGyroX",
        "scaledGyroY",
        "scaledGyroZ",
    )

    def __init__(
        self,
        timestamp: int,
        gpsCorrelTimestampFlags: int | None = None,
        gpsCorrelTimestampTow: float | None = None,
        gpsCorrelTimestampWeekNum: int | None = None,
        scaledAccelX: float | None = None,
        scaledAccelY: float | None = None,
        scaledAccelZ: float | None = None,
        scaledGyroX: float | None = None,
        scaledGyroY: float | None = None,
        scaledGyroZ: float | None = None,
    ):
        super().__init__(timestamp)

        self.gpsCorrelTimestampFlags = gpsCorrelTimestampFlags
        self.gpsCorrelTimestampTow = gpsCorrelTimestampTow
        self.gpsCorrelTimestampWeekNum = gpsCorrelTimestampWeekNum
        self.scaledAccelX = scaledAccelX
        self.scaledAccelY = scaledAccelY
        self.scaledAccelZ = scaledAccelZ
        self.scaledGyroX = scaledGyroX
        self.scaledGyroY = scaledGyroY
        self.scaledGyroZ = scaledGyroZ


class EstimatedDataPacket(IMUDataPacket):
    """
    Represents an estimated data packet from the IMU. These values are the processed values of the
    raw data that are supposed to be more accurate/smoothed. It contains a timestamp and the
    estimated values of the relevant data points.
    """

    __slots__ = (
        "estAngularRateX",
        "estAngularRateY",
        "estAngularRateZ",
        "estAttitudeUncertQuaternionW",
        "estAttitudeUncertQuaternionX",
        "estAttitudeUncertQuaternionY",
        "estAttitudeUncertQuaternionZ",
        "estCompensatedAccelX",
        "estCompensatedAccelY",
        "estCompensatedAccelZ",
        "estFilterDynamicsMode",
        "estFilterGpsTimeTow",  # Time of week
        "estFilterGpsTimeWeekNum",  # Week number
        "estFilterState",
        "estFilterStatusFlags",
        "estOrientQuaternionW",
        "estOrientQuaternionX",
        "estOrientQuaternionY",
        "estOrientQuaternionZ",
        "estPressureAlt",
    )

    def __init__(
        self,
        timestamp: int,
        estFilterGpsTimeTow: float | None = None,
        estFilterGpsTimeWeekNum: int | None = None,
        estOrientQuaternionW: float | None = None,
        estOrientQuaternionX: float | None = None,
        estOrientQuaternionY: float | None = None,
        estOrientQuaternionZ: float | None = None,
        estPressureAlt: float | None = None,
        estFilterState: int | None = None,
        estFilterDynamicsMode: int | None = None,
        estFilterStatusFlags: int | None = None,
        estAttitudeUncertQuaternionX: float | None = None,
        estAttitudeUncertQuaternionY: float | None = None,
        estAttitudeUncertQuaternionZ: float | None = None,
        estAttitudeUncertQuaternionW: float | None = None,
        estAngularRateX: float | None = None,
        estAngularRateY: float | None = None,
        estAngularRateZ: float | None = None,
        estCompensatedAccelX: float | None = None,
        estCompensatedAccelY: float | None = None,
        estCompensatedAccelZ: float | None = None,
    ):
        super().__init__(timestamp)

        self.estFilterGpsTimeTow = estFilterGpsTimeTow
        self.estFilterGpsTimeWeekNum = estFilterGpsTimeWeekNum
        self.estOrientQuaternionW = estOrientQuaternionW
        self.estOrientQuaternionX = estOrientQuaternionX
        self.estOrientQuaternionY = estOrientQuaternionY
        self.estOrientQuaternionZ = estOrientQuaternionZ
        self.estPressureAlt = estPressureAlt
        self.estFilterState = estFilterState
        self.estFilterDynamicsMode = estFilterDynamicsMode
        self.estFilterStatusFlags = estFilterStatusFlags
        self.estAttitudeUncertQuaternionX = estAttitudeUncertQuaternionW
        self.estAttitudeUncertQuaternionX = estAttitudeUncertQuaternionX
        self.estAttitudeUncertQuaternionX = estAttitudeUncertQuaternionY
        self.estAttitudeUncertQuaternionX = estAttitudeUncertQuaternionZ
        self.estAngularRateX = estAngularRateX
        self.estAngularRateY = estAngularRateY
        self.estAngularRateZ = estAngularRateZ
        self.estCompensatedAccelX = estCompensatedAccelX
        self.estCompensatedAccelY = estCompensatedAccelY
        self.estCompensatedAccelZ = estCompensatedAccelZ
