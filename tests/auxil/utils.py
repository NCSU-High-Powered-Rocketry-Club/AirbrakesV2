"""Utility functions used throughout the test suite."""

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket


def make_est_data_packet(**kwargs) -> EstimatedDataPacket:
    """Creates an EstimatedDataPacket with the specified keyword arguments. Provides dummy values
    for arguments not specified."""

    dummy_values = {k: 0.2 for k in EstimatedDataPacket.__struct_fields__}
    return EstimatedDataPacket(**{**dummy_values, **kwargs})


def make_raw_data_packet(**kwargs) -> RawDataPacket:
    """Creates a RawDataPacket with the specified keyword arguments. Provides dummy values for
    arguments not specified."""

    dummy_values = {k: 0.2 for k in RawDataPacket.__struct_fields__}
    return RawDataPacket(**{**dummy_values, **kwargs})


def make_processed_data_packet(**kwargs) -> ProcessedDataPacket:
    """Creates a ProcessedDataPacket with the specified keyword arguments. Provides dummy values
    for arguments not specified."""

    dummy_values = {k: 0.2 for k in ProcessedDataPacket.__struct_fields__}
    return ProcessedDataPacket(**{**dummy_values, **kwargs})
