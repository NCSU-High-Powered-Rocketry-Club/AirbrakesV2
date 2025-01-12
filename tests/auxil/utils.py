"""Utility functions used throughout the test suite."""

from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


def make_est_data_packet(**kwargs) -> EstimatedDataPacket:
    """Creates an EstimatedDataPacket with the specified keyword arguments. Provides dummy values
    for arguments not specified."""

    dummy_values = {k: 1.123456789 for k in EstimatedDataPacket.__struct_fields__}
    return EstimatedDataPacket(**{**dummy_values, **kwargs})


def make_raw_data_packet(**kwargs) -> RawDataPacket:
    """Creates a RawDataPacket with the specified keyword arguments. Provides dummy values for
    arguments not specified."""

    dummy_values = {k: 1.987654321 for k in RawDataPacket.__struct_fields__}
    return RawDataPacket(**{**dummy_values, **kwargs})


def make_processed_data_packet(**kwargs) -> ProcessorDataPacket:
    """Creates a ProcessedDataPacket with the specified keyword arguments. Provides dummy values
    for arguments not specified."""

    dummy_values = {k: 1.887766554 for k in ProcessorDataPacket.__struct_fields__}
    return ProcessorDataPacket(**{**dummy_values, **kwargs})


def make_context_data_packet(**kwargs) -> ContextDataPacket:
    """Creates a ContextDataPacket with the specified keyword arguments. Provides dummy values for
    arguments not specified."""

    dummy_values = {k: 2 for k in ContextDataPacket.__struct_fields__}
    return ContextDataPacket(**{**dummy_values, **kwargs})


def make_servo_data_packet(**kwargs) -> ServoDataPacket:
    """Creates a ServoDataPacket with the specified keyword arguments. Provides dummy values for
    arguments not specified."""

    dummy_values = {k: "0.2" for k in ServoDataPacket.__struct_fields__}
    return ServoDataPacket(**{**dummy_values, **kwargs})


def make_apogee_predictor_data_packet(**kwargs) -> ApogeePredictorDataPacket:
    """Creates an ApogeePredictorDataPacket with the specified keyword arguments. Provides dummy
    values for arguments not specified."""

    dummy_values = {k: 0.123456789 for k in ApogeePredictorDataPacket.__struct_fields__}
    return ApogeePredictorDataPacket(**{**dummy_values, **kwargs})
