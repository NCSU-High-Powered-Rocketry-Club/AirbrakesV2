import pytest

from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket


class TestEstimatedDataPacket:
    """
    Tests the EstimatedDataPacket class.
    """

    def test_estimated_data_packet_initialization(self):
        packet = EstimatedDataPacket(
            timestamp=123456789,
            estOrientQuaternionX=0.1,
            estOrientQuaternionY=0.2,
            estOrientQuaternionZ=0.3,
            estOrientQuaternionW=0.4,
            estPressureAlt=1013.25,
            estAttitudeUncertQuaternionW=0.04,
            estAttitudeUncertQuaternionX=0.01,
            estAttitudeUncertQuaternionY=0.02,
            estAttitudeUncertQuaternionZ=0.03,
            estAngularRateX=0.5,
            estAngularRateY=0.6,
            estAngularRateZ=0.7,
            estCompensatedAccelX=9.81,
            estCompensatedAccelY=0.0,
            estCompensatedAccelZ=-9.81,
            estLinearAccelX=0.0,
            estLinearAccelY=0.0,
            estLinearAccelZ=0.0,
            invalid_fields=["estOrientQuaternion"],
        )

        assert packet.timestamp == 123456789
        assert packet.invalid_fields == ["estOrientQuaternion"]
        assert packet.estOrientQuaternionW == 0.4
        assert packet.estOrientQuaternionX == 0.1
        assert packet.estOrientQuaternionY == 0.2
        assert packet.estOrientQuaternionZ == 0.3
        assert packet.estPressureAlt == 1013.25
        assert packet.estAttitudeUncertQuaternionW == 0.04
        assert packet.estAttitudeUncertQuaternionX == 0.01
        assert packet.estAttitudeUncertQuaternionY == 0.02
        assert packet.estAttitudeUncertQuaternionZ == 0.03
        assert packet.estAngularRateX == 0.5
        assert packet.estAngularRateY == 0.6
        assert packet.estAngularRateZ == 0.7
        assert packet.estCompensatedAccelX == 9.81
        assert packet.estCompensatedAccelY == 0.0
        assert packet.estCompensatedAccelZ == -9.81
        assert packet.estLinearAccelX == 0.0
        assert packet.estLinearAccelY == 0.0
        assert packet.estLinearAccelZ == 0.0

    def test_estimated_data_packet_defaults(self):
        packet = EstimatedDataPacket(timestamp=123456789)

        assert packet.timestamp == 123456789
        assert packet.invalid_fields is None
        assert packet.estOrientQuaternionW is None
        assert packet.estOrientQuaternionX is None
        assert packet.estOrientQuaternionY is None
        assert packet.estOrientQuaternionZ is None
        assert packet.estPressureAlt is None
        assert packet.estAttitudeUncertQuaternionW is None
        assert packet.estAttitudeUncertQuaternionX is None
        assert packet.estAttitudeUncertQuaternionY is None
        assert packet.estAttitudeUncertQuaternionZ is None
        assert packet.estAngularRateX is None
        assert packet.estAngularRateY is None
        assert packet.estAngularRateZ is None
        assert packet.estCompensatedAccelX is None
        assert packet.estCompensatedAccelY is None
        assert packet.estCompensatedAccelZ is None
        assert packet.estLinearAccelX is None
        assert packet.estLinearAccelY is None
        assert packet.estLinearAccelZ is None

    def test_required_fields(self):
        with pytest.raises(TypeError):
            EstimatedDataPacket()

    def test_wrong_type_does_not_raise_exception(self):
        EstimatedDataPacket(timestamp="12345.6789", estAngularRateX=object())


class TestRawDataPacket:
    """
    Tests the RawDataPacket class.
    """

    def test_raw_data_packet_initialization(self):
        packet = RawDataPacket(
            timestamp=123456789,
            invalid_fields=["scaledAccelX"],
            scaledAccelX=1.0,
            scaledAccelY=2.0,
            scaledAccelZ=3.0,
            scaledGyroX=4.0,
            scaledGyroY=5.0,
            scaledGyroZ=6.0,
        )

        assert packet.timestamp == 123456789
        assert packet.invalid_fields == ["scaledAccelX"]
        assert packet.scaledAccelX == 1.0
        assert packet.scaledAccelY == 2.0
        assert packet.scaledAccelZ == 3.0
        assert packet.scaledGyroX == 4.0
        assert packet.scaledGyroY == 5.0
        assert packet.scaledGyroZ == 6.0

    def test_raw_data_packet_defaults(self):
        packet = RawDataPacket(timestamp=123456789)

        assert packet.timestamp == 123456789
        assert packet.invalid_fields is None
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
        RawDataPacket(timestamp="12345.6789", scaledAccelX=object())
