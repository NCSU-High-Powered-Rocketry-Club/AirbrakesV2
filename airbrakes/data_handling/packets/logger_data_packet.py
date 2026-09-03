"""Module for describing the data packet for the logger to log."""

from typing import Literal

import msgspec


class LoggerDataPacket(msgspec.Struct, array_like=True, kw_only=True):
    """
    Represents a collection of all data that the logger can log in a line.

    Not every field will be filled in every packet. The order in which
    the fields are defined determines the order in which they will be
    logged.
    """

    # Fields derived from ContextDataPacket
    state_letter: str | None

    # Fields in ServoDataPacket
    set_extension: str | None
    battery_voltage: str | None
    current_milliamps: str | None

    # FIRMDataPacket Fields
    timestamp_seconds: float | None = None
    temperature_celsius: float | None = None
    pressure_pascals: float | None = None
    raw_acceleration_x_gs: float | None = None
    raw_acceleration_y_gs: float | None = None
    raw_acceleration_z_gs: float | None = None
    raw_rotated_acceleration_x_gs: float | None = None
    raw_rotated_acceleration_y_gs: float | None = None
    raw_rotated_acceleration_z_gs: float | None = None
    est_tilt_angle_degrees: float | None = None
    raw_angular_rate_x_deg_per_s: float | None = None
    raw_angular_rate_y_deg_per_s: float | None = None
    raw_angular_rate_z_deg_per_s: float | None = None
    magnetic_field_x_microteslas: float | None = None
    magnetic_field_y_microteslas: float | None = None
    magnetic_field_z_microteslas: float | None = None
    est_position_z_meters: float | None = None
    est_velocity_z_meters_per_s: float | None = None
    est_mach_number: float | None = None
    est_quaternion_w: float | None = None
    est_quaternion_x: float | None = None
    est_quaternion_y: float | None = None
    est_quaternion_z: float | None = None

    # ProcessorDataPacket Fields
    current_altitude: float | None = None
    integrating_for_altitude: Literal["T", "F"] | None = None
    vertical_velocity_meters_per_s: float | None = None
    horizontal_velocity_meters_per_s: float | None = None
    tilt_angle_degrees: float | None = None
    angular_rate_deg_per_s: float | None = None

    # Apogee Predictor Data Packet Fields
    predicted_apogee: float | None = None
    height_used_for_prediction: float | None = None
    vertical_velocity_meters_per_s_used_for_prediction: float | None = None
    horizontal_velocity_meters_per_s_used_for_prediction: float | None = None
    tilt_angle_degrees_used_for_prediction: float | None = None
    angular_rate_deg_per_s_used_for_prediction: float | None = None

    # Other fields in ContextDataPacket
    retrieved_firm_packets: int | None = None
    apogee_predictor_queue_size: int | None = None
    update_timestamp_ns: int | None = None
