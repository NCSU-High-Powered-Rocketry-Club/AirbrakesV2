"""Module for describing the datapackets from the IMU"""


class IMUDataPacket:
    """
    Represents a collection of data packets from the IMU. It contains the acceleration, velocity, altitude, yaw, pitch,
    roll of the rocket and the timestamp of the data. The attributes should be named the same as they are when sent from
    the IMU--this just means they're going to be in camelCase.
    """

    __slots__ = ("timestamp",)

    def __init__(self, timestamp: float):
        self.timestamp = timestamp


class RawDataPacket(IMUDataPacket):
    """
    Represents a raw data packet from the IMU. These values are exactly what the IMU read, without any processing.
    It contains a timestamp and the raw values of the acceleration, gyroscope, and GPS correlation data.
    """

    __slots__ = (
        "gpsCorrelTimestampFlags",
        "gpsCorrelTimestampTow",
        "gpsCorrelTimestampWeekNum",
        "scaledAccelX",
        "scaledAccelY",
        "scaledAccelZ",
        "scaledGyroX",
        "scaledGyroY",
        "scaledGyroZ",
    )

    def __init__(
        self,
        timestamp: float,
        gpsCorrelTimestampFlags: int | None = None,
        gpsCorrelTimestampTow: float | None = None,
        gpsCorrelTimestampWeekNum: int | None = None,
        scaledAccelX: float | None = None,
        scaledAccelY: float | None = None,
        scaledAccelZ: float | None = None,
        scaledGyroX: float | None = None,
        scaledGyroY: float | None = None,
        scaledGyroZ: float | None = None
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

    def __str__(self):
        return (
            f"RawDataPacket(timestamp={self.timestamp}, "
            f"gpsCorrelTimestampFlags={self.gpsCorrelTimestampFlags}, "
            f"gpsCorrelTimestampTow={self.gpsCorrelTimestampTow}, "
            f"gpsCorrelTimestampWeekNum={self.gpsCorrelTimestampWeekNum}, "
            f"scaledAccelX={self.scaledAccelX}, "
            f"scaledAccelY={self.scaledAccelY}, "
            f"scaledAccelZ={self.scaledAccelZ}, "
            f"scaledGyroX={self.scaledGyroX}, "
            f"scaledGyroY={self.scaledGyroY}, "
            f"scaledGyroZ={self.scaledGyroZ})"
        )


class EstimatedDataPacket(IMUDataPacket):
    """
    Represents an estimated data packet from the IMU. These values are the processed values of the raw data
    that are supposed to be more accurate/smoothed. It contains a timestamp and the estimated values of the relevant data points.
    """

    __slots__ = (
        "estAngularRateX",
        "estAngularRateY",
        "estAngularRateZ",
        "estAttitudeUncertQuaternion",
        "estCompensatedAccelX",
        "estCompensatedAccelY",
        "estCompensatedAccelZ",
        "estFilterDynamicsMode",
        "estFilterGpsTimeTow",
        "estFilterGpsTimeWeekNum",
        "estFilterState",
        "estFilterStatusFlags",
        "estOrientQuaternion",
        "estPressureAlt",
    )

    def __init__(
        self,
        timestamp: float,
        estFilterGpsTimeTow: float | None = None,
        estFilterGpsTimeWeekNum: int | None = None,
        estOrientQuaternion: tuple[float, float, float, float] | None = None,
        estPressureAlt: float | None = None,
        estFilterState: int | None = None,
        estFilterDynamicsMode: int | None = None,
        estFilterStatusFlags: int | None = None,
        estAttitudeUncertQuaternion: tuple[float, float, float, float] | None = None,
        estAngularRateX: float | None = None,
        estAngularRateY: float | None = None,
        estAngularRateZ: float | None = None,
        estCompensatedAccelX: float | None = None,
        estCompensatedAccelY: float | None = None,
        estCompensatedAccelZ: float | None = None
    ):
        super().__init__(timestamp)

        self.estFilterGpsTimeTow = estFilterGpsTimeTow
        self.estFilterGpsTimeWeekNum = estFilterGpsTimeWeekNum
        self.estOrientQuaternion = estOrientQuaternion
        self.estPressureAlt = estPressureAlt
        self.estFilterState = estFilterState
        self.estFilterDynamicsMode = estFilterDynamicsMode
        self.estFilterStatusFlags = estFilterStatusFlags
        self.estAttitudeUncertQuaternion = estAttitudeUncertQuaternion
        self.estAngularRateX = estAngularRateX
        self.estAngularRateY = estAngularRateY
        self.estAngularRateZ = estAngularRateZ
        self.estCompensatedAccelX = estCompensatedAccelX
        self.estCompensatedAccelY = estCompensatedAccelY
        self.estCompensatedAccelZ = estCompensatedAccelZ

    def __str__(self):
        return (
            f"EstimatedDataPacket(timestamp={self.timestamp}, "
            f"estFilterGpsTimeTow={self.estFilterGpsTimeTow}, "
            f"estFilterGpsTimeWeekNum={self.estFilterGpsTimeWeekNum}, "
            f"estOrientQuaternion={self.estOrientQuaternion}, "
            f"estPressureAlt={self.estPressureAlt}, "
            f"estFilterState={self.estFilterState}, "
            f"estFilterDynamicsMode={self.estFilterDynamicsMode}, "
            f"estFilterStatusFlags={self.estFilterStatusFlags}, "
            f"estAttitudeUncertQuaternion={self.estAttitudeUncertQuaternion}, "
            f"estAngularRateX={self.estAngularRateX}, "
            f"estAngularRateY={self.estAngularRateY}, "
            f"estAngularRateZ={self.estAngularRateZ}, "
            f"estCompensatedAccelX={self.estCompensatedAccelX}, "
            f"estCompensatedAccelY={self.estCompensatedAccelY}, "
            f"estCompensatedAccelZ={self.estCompensatedAccelZ})"
        )
