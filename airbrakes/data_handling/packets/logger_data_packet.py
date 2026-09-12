"""CSV row containing context, IMU, processor, predictor, and servo data."""

from typing import Literal

import msgspec


class LoggerDataPacket(msgspec.Struct, array_like=True, kw_only=True):
    """All values that may be recorded for an IMU data packet."""

    # Fields from ContextDataPacket
    state_letter: str | None

    # Fields from ServoDataPacket
    current_position: float | None = None
    current_temp: float | None = None
    voltage: float | None = None
    system_current_milliamps: float | None = None
    battery_volts: float | None = None

    # Fields from IMUDataPacket
    timestamp: int | None = None
    invalid_fields: str | None = None
    # Fields from RawDataPacket
    scaledAccelX: float | None = None
    scaledAccelY: float | None = None
    scaledAccelZ: float | None = None
    scaledGyroX: float | None = None
    scaledGyroY: float | None = None
    scaledGyroZ: float | None = None
    deltaVelX: float | None = None
    deltaVelY: float | None = None
    deltaVelZ: float | None = None
    deltaThetaX: float | None = None
    deltaThetaY: float | None = None
    deltaThetaZ: float | None = None
    scaledAmbientPressure: float | None = None

    # Fields in EstimatedDataPacket
    estPressureAlt: float | None = None
    estOrientQuaternionW: float | None = None
    estOrientQuaternionX: float | None = None
    estOrientQuaternionY: float | None = None
    estOrientQuaternionZ: float | None = None
    estAttitudeUncertQuaternionW: float | None = None
    estAttitudeUncertQuaternionX: float | None = None
    estAttitudeUncertQuaternionY: float | None = None
    estAttitudeUncertQuaternionZ: float | None = None
    estAngularRateX: float | None = None
    estAngularRateY: float | None = None
    estAngularRateZ: float | None = None
    estCompensatedAccelX: float | None = None
    estCompensatedAccelY: float | None = None
    estCompensatedAccelZ: float | None = None
    estLinearAccelX: float | None = None
    estLinearAccelY: float | None = None
    estLinearAccelZ: float | None = None
    estGravityVectorX: float | None = None
    estGravityVectorY: float | None = None
    estGravityVectorZ: float | None = None

    # Fields from ProcessorDataPacket
    current_altitude: float | None = None
    integrating_for_altitude: Literal["T", "F"] | None = None
    vertical_velocity_meters_per_s: float | None = None
    horizontal_velocity_meters_per_s: float | None = None
    tilt_angle_degrees: float | None = None
    angular_rate_deg_per_s: float | None = None
    timestamp_seconds: float | None = None

    # Fields from PredictorDataPacket
    predicted_apogee: float | None = None
    height_used_for_prediction: float | None = None
    vertical_velocity_meters_per_s_used_for_prediction: float | None = None
    horizontal_velocity_meters_per_s_used_for_prediction: float | None = None
    tilt_angle_degrees_used_for_prediction: float | None = None
    angular_rate_deg_per_s_used_for_prediction: float | None = None

    # Other fields from ContextDataPacket
    retrieved_imu_packets: int | None = None
    queued_imu_packets: int | None = None
    imu_packets_per_cycle: int | None = None
    apogee_predictor_queue_size: int | None = None
    update_timestamp_ns: int | None = None
