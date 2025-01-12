import pytest

from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


@pytest.fixture
def logged_data_packet():
    return LoggerDataPacket(
        state_letter=TestLoggedDataPacket.state_letter,
        set_extension=TestLoggedDataPacket.set_extension,
        timestamp=TestLoggedDataPacket.timestamp,
    )


class TestLoggedDataPacket:
    """Tests for the LoggedDataPacket class."""

    state_letter = "test"
    set_extension = "0.0"
    timestamp = 10

    def test_init(self, logged_data_packet):
        packet = logged_data_packet
        assert isinstance(packet, dict)
        assert packet["state_letter"] == self.state_letter
        assert packet["set_extension"] == self.set_extension
        assert packet["timestamp"] == self.timestamp

    def test_logged_data_packet_has_all_fields_of_data_packets(self):
        """Tests whether the LoggedDataPacket class has all the fields of the data packet
        classes."""
        log_dp_fields = set(LoggerDataPacket.__annotations__)

        context_dp_fields = set(ContextDataPacket.__struct_fields__)
        servo_dp_fields = set(ServoDataPacket.__struct_fields__)
        est_dp_fields = set(EstimatedDataPacket.__struct_fields__)
        raw_dp_fields = set(RawDataPacket.__struct_fields__)
        proc_dp_fields = set(ProcessorDataPacket.__struct_fields__)
        apogee_predictor_dp_fields = set(ApogeePredictorDataPacket.__struct_fields__)

        # remove one field from proc_dp_fields:
        proc_dp_fields.remove("time_since_last_data_packet")

        assert servo_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {servo_dp_fields - log_dp_fields}"
        assert est_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {est_dp_fields - log_dp_fields}"
        assert raw_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {raw_dp_fields - log_dp_fields}"
        assert proc_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {proc_dp_fields - log_dp_fields}"
        assert apogee_predictor_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {apogee_predictor_dp_fields - log_dp_fields}"
        assert context_dp_fields.issubset(
            log_dp_fields
        ), f"Missing fields: {context_dp_fields - log_dp_fields}"

        available_fields = (
            est_dp_fields.union(raw_dp_fields)
            .union(proc_dp_fields)
            .union(context_dp_fields)
            .union(servo_dp_fields)
            .union(apogee_predictor_dp_fields)
        )
        assert (
            log_dp_fields == available_fields
        ), f"Extra fields: {log_dp_fields - available_fields}"

    def test_logged_data_packet_field_order(self):
        """Tests whether the LoggedDataPacket class has the correct field order."""

        # Only context data packet has a different order - one field - "state_letter" is in the
        # beginning, the rest at the end.

        log_dp_fields = list(LoggerDataPacket.__annotations__)
        context_dp_fields = list(ContextDataPacket.__struct_fields__)
        servo_dp_fields = list(ServoDataPacket.__struct_fields__)
        raw_dp_fields = list(RawDataPacket.__struct_fields__)
        est_dp_fields = list(EstimatedDataPacket.__struct_fields__)
        proc_dp_fields = list(ProcessorDataPacket.__struct_fields__)
        apogee_predictor_dp_fields = list(ApogeePredictorDataPacket.__struct_fields__)

        proc_dp_fields.remove("time_since_last_data_packet")
        # Remove the base class IMUDataPacket fields from the list:
        est_dp_fields.remove("timestamp")
        est_dp_fields.remove("invalid_fields")

        assert log_dp_fields[0] == context_dp_fields[0]
        assert (
            log_dp_fields[1:]
            == servo_dp_fields
            + raw_dp_fields
            + est_dp_fields
            + proc_dp_fields
            + apogee_predictor_dp_fields
            + context_dp_fields[1:]
        )
