"""
Utility functions used throughout the test suite.
"""

from firm_client import FIRMDataPacket
from msgspec.structs import asdict

from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


def make_firm_data_packet(**kwargs) -> FIRMDataPacket:
    """
    Creates a FIRMDataPacket with the specified keyword arguments.
    Provides dummy values for arguments not specified.
    """
    dummy_values = dict.fromkeys(FIRMDataPacket.__struct_fields__, 1.987654321)
    return FIRMDataPacket(**{**dummy_values, **kwargs})


def make_firm_data_packet_zeroed(**kwargs) -> FIRMDataPacket:
    """
    Creates a FIRMDataPacket with the specified keyword arguments.
    Provides zeroes for arguments not specified.
    """
    dummy_values = dict.fromkeys(FIRMDataPacket.__struct_fields__, 0.0)
    return FIRMDataPacket(**{**dummy_values, **kwargs})


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


def context_packet_to_logger_kwargs(ctx_packet) -> dict:
    """
    Converts a ContextDataPacket to a dictionary suitable for logging.
    """
    d = asdict(ctx_packet).copy()
    state_type = d.pop("state")
    d["state_letter"] = state_type.__name__[0]  # "S", "M", "C", "F", "L"
    return d
