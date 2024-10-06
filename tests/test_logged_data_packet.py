import pytest

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket


@pytest.fixture
def logged_data_packet():
    return LoggedDataPacket(
        state=TestLoggedDataPacket.state,
        extension=TestLoggedDataPacket.extension,
        timestamp=TestLoggedDataPacket.timestamp,
    )


class TestLoggedDataPacket:
    """Tests for the LoggedDataPacket class."""

    state = "test"
    extension = 0.0
    timestamp = 0.0

    def test_init(self, logged_data_packet):
        packet = logged_data_packet
        assert packet.state == self.state
        assert packet.extension == self.extension
        assert packet.timestamp == self.timestamp

    def test_required_args(self):
        with pytest.raises(TypeError):
            LoggedDataPacket()

    def test_logged_data_packet_has_all_fields_of_imu_data_packet(self):
        """Tests whether the LoggedDataPacket class has all the fields of the IMUDataPacket classes."""
        est_dp_fields = set(EstimatedDataPacket.__struct_fields__)
        raw_dp_fields = set(RawDataPacket.__struct_fields__)
        log_dp_fields = set(LoggedDataPacket.__struct_fields__)
        proc_dp_fields = set(ProcessedDataPacket.__struct_fields__)

        extra_fields = {"state", "extension", "timestamp"}

        assert est_dp_fields.issubset(log_dp_fields), f"Missing fields: {est_dp_fields - log_dp_fields}"
        assert raw_dp_fields.issubset(log_dp_fields), f"Missing fields: {raw_dp_fields - log_dp_fields}"
        assert proc_dp_fields.issubset(log_dp_fields), f"Missing fields: {proc_dp_fields - log_dp_fields}"

        available_fields = est_dp_fields.union(raw_dp_fields).union(proc_dp_fields).union(extra_fields)
        assert log_dp_fields == available_fields, f"Extra fields: {log_dp_fields - available_fields}"

    def test_set_imu_data_packet_attributes(self, logged_data_packet):
        """Tests whether the set_imu_data_packet_attributes method sets the attributes correctly,
        along with proper rounding of the float values."""
        packet = logged_data_packet
        est_data_packet = EstimatedDataPacket(
            timestamp=3 + 1e9, estPressureAlt=1.234567891, estAngularRateX=0.8885554448, estOrientQuaternionW=0.4445
        )
        raw_data_packet = RawDataPacket(
            timestamp=4 + 1e9, scaledAccelY=1.0923457654, deltaThetaY=1.6768972567, scaledGyroZ=0.12345
        )

        packet.set_imu_data_packet_attributes(est_data_packet)
        assert packet.timestamp == 3.0 + 1e9
        assert packet.state == "test"
        assert packet.extension == 0.0
        assert packet.estPressureAlt == 1.23456789
        assert packet.estAngularRateX == 0.88855544
        assert packet.estOrientQuaternionW == 0.4445

        packet.set_imu_data_packet_attributes(raw_data_packet)
        assert packet.timestamp == 4.0 + 1e9
        assert packet.state == "test"
        assert packet.extension == 0.0
        assert packet.scaledAccelY == 1.09234577
        assert packet.deltaThetaY == 1.67689726
        assert packet.scaledGyroZ == 0.12345

    def test_set_processed_data_packet_attributes(self, logged_data_packet):
        """Tests whether the set_processed_data_packet_attributes method sets the attributes correctly"""
        packet = logged_data_packet
        proc_data_packet = ProcessedDataPacket(
            avg_acceleration=(1.234567891, 0.8885554448, 0.4445),
            current_altitude=1.0923457654,
            speed=1.6768972567,
        )

        packet.set_processed_data_packet_attributes(proc_data_packet)
        assert packet.avg_acceleration == (1.234567891, 0.8885554448, 0.4445)
        assert packet.current_altitude == 1.0923457654
        assert packet.speed == 1.6768972567
        assert packet.timestamp == 0.0
        assert packet.state == "test"
        assert packet.extension == 0.0
        assert packet.estPressureAlt is None
        assert packet.estAngularRateX is None
        assert packet.estOrientQuaternionW is None
        assert packet.scaledAccelY is None
        assert packet.deltaThetaY is None
        assert packet.scaledGyroZ is None
