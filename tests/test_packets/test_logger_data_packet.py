"""Tests for the IMU logger schema."""

from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


def test_logger_packet_contains_all_source_and_derived_fields():
    logger_fields = set(LoggerDataPacket.__struct_fields__)
    assert set(RawDataPacket.__struct_fields__).issubset(logger_fields)
    assert set(EstimatedDataPacket.__struct_fields__).issubset(logger_fields)
    assert set(ProcessorDataPacket.__struct_fields__).issubset(logger_fields)
    assert set(ServoDataPacket.__struct_fields__).issubset(logger_fields)
    assert (set(ContextDataPacket.__struct_fields__) - {"state"}).issubset(logger_fields)
    assert "state_letter" in logger_fields
