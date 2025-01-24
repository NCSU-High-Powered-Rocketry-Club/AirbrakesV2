"""Module for describing the data packet for the logger to log"""

from typing import TypedDict


class LoggerDataPacket(TypedDict, total=False):  # total=False means all fields are NotRequired
    """
    Represents a collection of all data that the logger can log in a line. Not every field will be
    filled in every packet. The order in which the fields are defined determines the order in which
    they will be logged.
    """

    # Field in ContextDataPacket
    state_letter: str | None

    # Fields in ServoDataPacket
    set_extension: str | None
    encoder_position: str | None

    # IMU Data Packet Fields
    timestamp: int
    invalid_fields: list[str] | None

    # Raw Data Packet Fields
    scaledAccelX: float | None
    scaledAccelY: float | None
    scaledAccelZ: float | None
    scaledGyroX: float | None
    scaledGyroY: float | None
    scaledGyroZ: float | None
    deltaVelX: float | None
    deltaVelY: float | None
    deltaVelZ: float | None
    deltaThetaX: float | None
    deltaThetaY: float | None
    deltaThetaZ: float | None
    scaledAmbientPressure: float | None

    # Estimated Data Packet Fields
    estOrientQuaternionW: float | None
    estOrientQuaternionX: float | None
    estOrientQuaternionY: float | None
    estOrientQuaternionZ: float | None
    estPressureAlt: float | None
    estAttitudeUncertQuaternionW: float | None
    estAttitudeUncertQuaternionX: float | None
    estAttitudeUncertQuaternionY: float | None
    estAttitudeUncertQuaternionZ: float | None
    estAngularRateX: float | None
    estAngularRateY: float | None
    estAngularRateZ: float | None
    estCompensatedAccelX: float | None
    estCompensatedAccelY: float | None
    estCompensatedAccelZ: float | None
    estLinearAccelX: float | None
    estLinearAccelY: float | None
    estLinearAccelZ: float | None
    estGravityVectorX: float | None
    estGravityVectorY: float | None
    estGravityVectorZ: float | None

    # Processor Data Packet Fields
    current_altitude: float | None
    vertical_velocity: float | None
    vertical_acceleration: float | None

    # Apogee Predictor Data Packet Fields
    predicted_apogee: float | None
    a_coefficient: float | None
    b_coefficient: float | None
    uncertainty_threshold_1: float | None
    uncertainty_threshold_2: float | None

    # Other fields in ContextDataPacket
    batch_number: int | None
    imu_queue_size: int | None
    apogee_predictor_queue_size: int | None
