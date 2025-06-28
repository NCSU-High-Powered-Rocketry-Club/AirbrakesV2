"""
Module for describing the data packet for the logger to log.
"""

import msgspec


class LoggerDataPacket(msgspec.Struct, array_like=True, kw_only=True):
    """
    Represents a collection of all data that the logger can log in a line.

    Not every field will be filled in every packet. The order in which the fields are defined
    determines the order in which they will be logged.
    """

    # Field in ContextDataPacket
    state_letter: str | None

    # Fields in ServoDataPacket
    set_extension: str | None
    encoder_position: int | None

    # IMU Data Packet Fields
    timestamp: int
    invalid_fields: str | None

    # Raw Data Packet Fields
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

    # Estimated Data Packet Fields
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

    # Processor Data Packet Fields
    current_altitude: float | None = None
    vertical_velocity: float | None = None
    vertical_acceleration: float | None = None

    # Apogee Predictor Data Packet Fields
    # These fields are "str" because they were numpy.float64, which is converted to a string
    # when encoded in the logger. Encoding directly to string with 8 decimal places truncation.
    predicted_apogee: str | None = None
    a_coefficient: str | None = None
    b_coefficient: str | None = None
    uncertainty_threshold_1: str | None = None
    uncertainty_threshold_2: str | None = None

    # Other fields in ContextDataPacket
    retrieved_imu_packets: int | None
    queued_imu_packets: int | None
    apogee_predictor_queue_size: int | None
    imu_packets_per_cycle: int | None
    update_timestamp_ns: int | None
