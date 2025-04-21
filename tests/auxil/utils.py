"""Utility functions used throughout the test suite."""

from airbrakes.telemetry.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.telemetry.packets.logger_data_packet import LoggerDataPacket
from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.telemetry.packets.servo_data_packet import ServoDataPacket


def make_est_data_packet(**kwargs) -> EstimatedDataPacket:
    """
    Creates an EstimatedDataPacket with the specified keyword arguments.

    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(EstimatedDataPacket.__struct_fields__, 1.123456789)
    dummy_values["timestamp"] = kwargs.get("timestamp", 12345678)  # Needs to be an integer
    dummy_values["invalid_fields"] = None  # Needs to be a list or None
    return EstimatedDataPacket(**{**dummy_values, **kwargs})


def make_raw_data_packet(**kwargs) -> RawDataPacket:
    """
    Creates a RawDataPacket with the specified keyword arguments.

    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(RawDataPacket.__struct_fields__, 1.987654321)
    dummy_values["timestamp"] = kwargs.get("timestamp", 12345678)  # Needs to be an integer
    dummy_values["invalid_fields"] = None  # Needs to be a list or None
    return RawDataPacket(**{**dummy_values, **kwargs})


def make_processor_data_packet(**kwargs) -> ProcessorDataPacket:
    """
    Creates a ProcessorDataPacket with the specified keyword arguments.

    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(ProcessorDataPacket.__struct_fields__, 1.887766554)
    return ProcessorDataPacket(**{**dummy_values, **kwargs})


def make_context_data_packet(**kwargs) -> ContextDataPacket:
    """
    Creates a ContextDataPacket with the specified keyword arguments.

    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(ContextDataPacket.__struct_fields__, 2)
    return ContextDataPacket(**{**dummy_values, **kwargs})


def make_servo_data_packet(**kwargs) -> ServoDataPacket:
    """
    Creates a ServoDataPacket with the specified keyword arguments.

    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(ServoDataPacket.__struct_fields__, "0.2")
    return ServoDataPacket(**{**dummy_values, **kwargs})


def make_apogee_predictor_data_packet(**kwargs) -> ApogeePredictorDataPacket:
    """
    Creates an ApogeePredictorDataPacket with the specified keyword arguments.

    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(ApogeePredictorDataPacket.__struct_fields__, 0.123456789)
    return ApogeePredictorDataPacket(**{**dummy_values, **kwargs})


def make_logger_data_packet(**kwargs) -> LoggerDataPacket:
    """
    Creates a LoggerDataPacket with the specified keyword arguments.

    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(LoggerDataPacket.__struct_fields__, "test")
    return LoggerDataPacket(**{**dummy_values, **kwargs})
