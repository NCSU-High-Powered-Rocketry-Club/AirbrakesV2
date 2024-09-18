import pytest

from airbrakes.imu.imu_data_packet import EstimatedDataPacket, RawDataPacket


class TestEstimatedDataPacket:
    """Tests the EstimatedDataPacket class"""

    def test_estimated_data_packet_initialization(self):
        packet = EstimatedDataPacket(
            timestamp=123456789,
            estFilterGpsTimeTow=1234.56,
            estFilterGpsTimeWeekNum=42,
            estOrientQuaternionX=0.1,
            estOrientQuaternionY=0.2,
            estOrientQuaternionZ=0.3,
            estOrientQuaternionW=0.4,
            estPressureAlt=1013.25,
            estFilterState=1,
            estFilterDynamicsMode=2,
            estFilterStatusFlags=3,
            estAttitudeUncertQuaternionX=0.01,
            estAttitudeUncertQuaternionY=0.02,
            estAttitudeUncertQuaternionZ=0.03,
            estAttitudeUncertQuaternionW=0.04,
            estAngularRateX=0.5,
            estAngularRateY=0.6,
            estAngularRateZ=0.7,
            estCompensatedAccelX=9.81,
            estCompensatedAccelY=0.0,
            estCompensatedAccelZ=-9.81,
        )

        assert packet.timestamp == 123456789
        assert packet.estFilterGpsTimeTow == 1234.56
        assert packet.estFilterGpsTimeWeekNum == 42
        assert packet.estOrientQuaternionX == 0.1
        assert packet.estOrientQuaternionY == 0.2
        assert packet.estOrientQuaternionZ == 0.3
        assert packet.estOrientQuaternionW == 0.4
        assert packet.estPressureAlt == 1013.25
        assert packet.estFilterState == 1
        assert packet.estFilterDynamicsMode == 2
        assert packet.estFilterStatusFlags == 3
        assert packet.estAttitudeUncertQuaternionX == 0.01
        assert packet.estAttitudeUncertQuaternionY == 0.02
        assert packet.estAttitudeUncertQuaternionZ == 0.03
        assert packet.estAttitudeUncertQuaternionW == 0.04
        assert packet.estAngularRateX == 0.5
        assert packet.estAngularRateY == 0.6
        assert packet.estAngularRateZ == 0.7
        assert packet.estCompensatedAccelX == 9.81
        assert packet.estCompensatedAccelY == 0.0
        assert packet.estCompensatedAccelZ == -9.81

    def test_estimated_data_packet_defaults(self):
        packet = EstimatedDataPacket(timestamp=123456789)

        assert packet.timestamp == 123456789
        assert packet.estFilterGpsTimeTow is None
        assert packet.estFilterGpsTimeWeekNum is None
        assert packet.estOrientQuaternionX is None
        assert packet.estOrientQuaternionY is None
        assert packet.estOrientQuaternionZ is None
        assert packet.estOrientQuaternionW is None
        assert packet.estPressureAlt is None
        assert packet.estFilterState is None
        assert packet.estFilterDynamicsMode is None
        assert packet.estFilterStatusFlags is None
        assert packet.estAttitudeUncertQuaternionX is None
        assert packet.estAttitudeUncertQuaternionY is None
        assert packet.estAttitudeUncertQuaternionZ is None
        assert packet.estAttitudeUncertQuaternionW is None
        assert packet.estAngularRateX is None
        assert packet.estAngularRateY is None
        assert packet.estAngularRateZ is None
        assert packet.estCompensatedAccelX is None
        assert packet.estCompensatedAccelY is None
        assert packet.estCompensatedAccelZ is None

    def test_required_fields(self):
        with pytest.raises(TypeError):
            EstimatedDataPacket()

    def test_wrong_type_does_not_raise_exception(self):
        EstimatedDataPacket(timestamp="12345.6789", estFilterGpsTimeTow=object())


class TestRawDataPacket:
    """Tests the RawDataPacket class"""

    def test_raw_data_packet_initialization(self):
        packet = RawDataPacket(
            timestamp=123456789,
            gpsCorrelTimestampFlags=1,
            gpsCorrelTimestampTow=1234.56,
            gpsCorrelTimestampWeekNum=42,
            scaledAccelX=1.0,
            scaledAccelY=2.0,
            scaledAccelZ=3.0,
            scaledGyroX=4.0,
            scaledGyroY=5.0,
            scaledGyroZ=6.0,
        )

        assert packet.timestamp == 123456789
        assert packet.gpsCorrelTimestampFlags == 1
        assert packet.gpsCorrelTimestampTow == 1234.56
        assert packet.gpsCorrelTimestampWeekNum == 42
        assert packet.scaledAccelX == 1.0
        assert packet.scaledAccelY == 2.0
        assert packet.scaledAccelZ == 3.0
        assert packet.scaledGyroX == 4.0
        assert packet.scaledGyroY == 5.0
        assert packet.scaledGyroZ == 6.0

    def test_raw_data_packet_defaults(self):
        packet = RawDataPacket(timestamp=123456789)

        assert packet.timestamp == 123456789
        assert packet.gpsCorrelTimestampFlags is None
        assert packet.gpsCorrelTimestampTow is None
        assert packet.gpsCorrelTimestampWeekNum is None
        assert packet.scaledAccelX is None
        assert packet.scaledAccelY is None
        assert packet.scaledAccelZ is None
        assert packet.scaledGyroX is None
        assert packet.scaledGyroY is None
        assert packet.scaledGyroZ is None

    def test_required_fields(self):
        with pytest.raises(TypeError):
            RawDataPacket()

    def test_wrong_type_does_not_raise_exception(self):
        RawDataPacket(timestamp="12345.6789", gpsCorrelTimestampTow=object())
