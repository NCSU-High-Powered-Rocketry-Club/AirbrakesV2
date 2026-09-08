"""Factories for packet objects used by tests."""

from msgspec.structs import asdict

from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


def make_estimated_data_packet(**kwargs) -> EstimatedDataPacket:
    """Create an estimated packet whose stationary defaults require no velocity integration."""
    defaults = {
        "timestamp": 0,
        "estPressureAlt": 0.0,
        "estOrientQuaternionW": 1.0,
        "estOrientQuaternionX": 0.0,
        "estOrientQuaternionY": 0.0,
        "estOrientQuaternionZ": 0.0,
        "estAngularRateX": 0.0,
        "estAngularRateY": 0.0,
        "estAngularRateZ": 0.0,
        "estCompensatedAccelX": 0.0,
        "estCompensatedAccelY": 0.0,
        "estCompensatedAccelZ": -9.81,
        "estGravityVectorX": 0.0,
        "estGravityVectorY": 0.0,
        "estGravityVectorZ": -9.81,
    }
    return EstimatedDataPacket(**{**defaults, **kwargs})


def make_raw_data_packet(**kwargs) -> RawDataPacket:
    """Create a raw IMU data packet with zero-valued sensor defaults."""
    defaults = {"timestamp": 0}
    return RawDataPacket(**{**defaults, **kwargs})


def make_processor_data_packet(**kwargs) -> ProcessorDataPacket:
    """Create a processor packet with nonzero defaults."""
    defaults = {
        field: "F" if field == "integrating_for_altitude" else 1.987654321
        for field in ProcessorDataPacket.__struct_fields__
    }
    return ProcessorDataPacket(**{**defaults, **kwargs})


def make_processor_data_packet_zeroed(**kwargs) -> ProcessorDataPacket:
    """Create a processor packet with zero defaults."""
    defaults = {
        field: "F" if field == "integrating_for_altitude" else 0.0
        for field in ProcessorDataPacket.__struct_fields__
    }
    return ProcessorDataPacket(**{**defaults, **kwargs})


def make_context_data_packet(**kwargs) -> ContextDataPacket:
    """Create a context packet with dummy values."""
    defaults = dict.fromkeys(ContextDataPacket.__struct_fields__, 2)
    return ContextDataPacket(**{**defaults, **kwargs})


def make_servo_data_packet(**kwargs) -> ServoDataPacket:
    """Create a servo packet with dummy values."""
    defaults = dict.fromkeys(ServoDataPacket.__struct_fields__, "0.2")
    return ServoDataPacket(**{**defaults, **kwargs})


def make_apogee_predictor_data_packet(**kwargs) -> ApogeePredictorDataPacket:
    """Create an apogee predictor packet with dummy values."""
    defaults = dict.fromkeys(ApogeePredictorDataPacket.__struct_fields__, 0.123456789)
    return ApogeePredictorDataPacket(**{**defaults, **kwargs})


def make_logger_data_packet(**kwargs) -> LoggerDataPacket:
    """Create a logger packet with dummy values."""
    defaults = dict.fromkeys(LoggerDataPacket.__struct_fields__, "test")
    return LoggerDataPacket(**{**defaults, **kwargs})


def context_packet_to_logger_kwargs(ctx_packet: ContextDataPacket) -> dict:
    """Convert a context packet to logger-compatible field names."""
    values = asdict(ctx_packet).copy()
    state_type = values.pop("state")
    values["state_letter"] = state_type.__name__[0]
    return values
