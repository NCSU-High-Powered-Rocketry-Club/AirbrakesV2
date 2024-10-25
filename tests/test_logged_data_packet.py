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

    @pytest.mark.parametrize(
        "imu_data_packet",
        [
            EstimatedDataPacket(timestamp=3.0 + 1e9, invalid_fields=["test_1"]),
            RawDataPacket(timestamp=4.0 + 1e9, invalid_fields=["test_2"]),
        ],
        ids=["EstimatedDataPacket", "RawDataPacket"],
    )
    def test_set_imu_data_packet_attributes(self, logged_data_packet, imu_data_packet):
        """Tests whether the set_imu_data_packet_attributes method sets the attributes correctly,
        along with proper rounding of the float values."""
        packet = logged_data_packet

        # simulate setting all the fields of the imu_data_packet
        for i in imu_data_packet.__struct_fields__:
            if i in ["timestamp", "invalid_fields"]:
                continue  # this is not set in set_imu_data_packet_attributes
            setattr(imu_data_packet, i, 1.2345678910)

        packet.set_imu_data_packet_attributes(imu_data_packet)

        if isinstance(imu_data_packet, EstimatedDataPacket):
            assert packet.invalid_fields == ["test_1"]
        else:
            assert packet.invalid_fields == ["test_2"]

        assert packet.state == "test"
        assert packet.extension == 0.0
        # set_imu_data_packet_attributes should not set timestamp
        assert packet.timestamp == 0.0

        # check if all the fields are set correctly:
        for i in imu_data_packet.__struct_fields__:
            if i in ["timestamp", "invalid_fields"]:
                continue  # already tested above
            # test rounding of the float values:
            assert getattr(packet, i) == "1.23456789", f"{i} is not set correctly"

    def test_set_processed_data_packet_attributes(self, logged_data_packet):
        """Tests whether the set_processed_data_packet_attributes method sets the attributes correctly"""
        packet = logged_data_packet
        proc_data_packet = ProcessedDataPacket(
            current_altitude=1.0923457654,
            velocity=1.6768972567,
        )

        packet.set_processed_data_packet_attributes(proc_data_packet)
        assert packet.current_altitude == 1.0923457654
        assert packet.velocity == 1.6768972567
        assert packet.timestamp == 0.0
        assert packet.state == "test"
        assert packet.extension == 0.0
        assert packet.estPressureAlt is None
        assert packet.estAngularRateX is None
        assert packet.estOrientQuaternionW is None
        assert packet.scaledAccelY is None
        assert packet.deltaThetaY is None
        assert packet.scaledGyroZ is None
