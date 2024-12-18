import pytest

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket


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
    extension = "0.0"
    timestamp = 10

    def test_init(self, logged_data_packet):
        packet = logged_data_packet
        assert isinstance(packet, dict)
        assert packet["state"] == self.state
        assert packet["extension"] == self.extension
        assert packet["timestamp"] == self.timestamp

    def test_logged_data_packet_has_all_fields_of_imu_data_packet(self):
        """Tests whether the LoggedDataPacket class has all the fields of the IMUDataPacket
        classes."""
        est_dp_fields = set(EstimatedDataPacket.__struct_fields__)
        raw_dp_fields = set(RawDataPacket.__struct_fields__)
        log_dp_fields = set(LoggedDataPacket.__annotations__)
        proc_dp_fields = {"current_altitude", "vertical_velocity", "vertical_acceleration"}

        extra_fields = {"state", "extension", "timestamp", "predicted_apogee"}

        assert est_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {est_dp_fields - log_dp_fields}"
        assert raw_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {raw_dp_fields - log_dp_fields}"
        assert proc_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {proc_dp_fields - log_dp_fields}"

        available_fields = (
            est_dp_fields.union(raw_dp_fields).union(proc_dp_fields).union(extra_fields)
        )
        assert (
            log_dp_fields == available_fields
        ), f"Extra fields: {log_dp_fields - available_fields}"
