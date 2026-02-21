import pytest
from firm_client import FIRMDataPacket

from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket
from tests.auxil.utils import make_logger_data_packet


@pytest.fixture
def logger_data_packet():
    return make_logger_data_packet()


class TestLoggerDataPacket:
    """Tests for the LoggerDataPacket class."""

    def test_init(self, logger_data_packet):
        packet = logger_data_packet
        assert isinstance(packet, LoggerDataPacket)

    def test_logger_data_packet_has_all_fields_of_data_packets(self):
        """
        Tests whether the LoggerDataPacket class has all the fields of the
        data packet classes.
        """
        log_dp_fields = set(LoggerDataPacket.__struct_fields__)

        context_dp_fields = set(ContextDataPacket.__struct_fields__)
        servo_dp_fields = set(ServoDataPacket.__struct_fields__)
        firm_dp_fields = set(FIRMDataPacket.__struct_fields__)
        apogee_predictor_dp_fields = set(ApogeePredictorDataPacket.__struct_fields__)

        # Map Context 'state' -> Logger 'state_letter' for comparisons
        context_dp_fields_mapped = {
            ("state_letter" if f == "state" else f) for f in context_dp_fields
        }

        assert servo_dp_fields.issubset(log_dp_fields), (
            f"Missing fields: {servo_dp_fields - log_dp_fields}"
        )
        assert firm_dp_fields.issubset(log_dp_fields), (
            f"Missing fields: {firm_dp_fields - log_dp_fields}"
        )
        assert apogee_predictor_dp_fields.issubset(log_dp_fields), (
            f"Missing fields: {apogee_predictor_dp_fields - log_dp_fields}"
        )
        assert context_dp_fields_mapped.issubset(log_dp_fields), (
            f"Missing fields: {context_dp_fields_mapped - log_dp_fields}"
        )

        available_fields = (
            firm_dp_fields.union(context_dp_fields_mapped)
            .union(servo_dp_fields)
            .union(apogee_predictor_dp_fields)
        )
        assert log_dp_fields == available_fields, (
            f"Extra fields: {log_dp_fields - available_fields}"
        )

    def test_logger_data_packet_field_order(self):
        """
        Tests whether the LoggerDataPacket class has the correct field
        order.
        """
        # Only Context Data Packet has a different order - one field - "state_letter" is in the
        # beginning, the rest at the end.

        log_dp_fields = list(LoggerDataPacket.__struct_fields__)
        context_dp_fields = list(ContextDataPacket.__struct_fields__)
        servo_dp_fields = list(ServoDataPacket.__struct_fields__)
        firm_dp_fields = list(FIRMDataPacket.__struct_fields__)
        apogee_predictor_dp_fields = list(ApogeePredictorDataPacket.__struct_fields__)

        assert (
            log_dp_fields[1:]
            == servo_dp_fields + firm_dp_fields + apogee_predictor_dp_fields + context_dp_fields[1:]
        )
