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
        gpsCorrelTimestampFlags: int,
        gpsCorrelTimestampTow: float,
        gpsCorrelTimestampWeekNum: int,
        scaledAccelX: float,
        scaledAccelY: float,
        scaledAccelZ: float,
        scaledGyroX: float,
        scaledGyroY: float,
        scaledGyroZ: float
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
    Represents an estimated data packet from the IMU, these values are the processed values of the raw data that are
    supposed to be more accurate/smoothed. It contains a timestamp and the estimated values of the relevant data points.
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
        estFilterGpsTimeTow: float,
        estFilterGpsTimeWeekNum: int,
        estOrientQuaternion: tuple[float, float, float, float],
        estPressureAlt: float,
        estFilterState: int,
        estFilterDynamicsMode: int,
        estFilterStatusFlags: int,
        estAttitudeUncertQuaternion: tuple[float, float, float, float],
        estAngularRateX: float,
        estAngularRateY: float,
        estAngularRateZ: float,
        estCompensatedAccelX: float,
        estCompensatedAccelY: float,
        estCompensatedAccelZ: float
    ):
        super().__init__(timestamp)  # Use the provided timestamp

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
