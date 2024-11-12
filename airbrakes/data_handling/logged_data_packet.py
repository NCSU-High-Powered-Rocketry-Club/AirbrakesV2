"""Module for describing the data packet for the logger to log"""

from typing import Required, TypedDict


class LoggedDataPacket(TypedDict, total=False):  # total=False means all fields are NotRequired
    """
    Represents a collection of all data that the logger can log in a line. Not every field will be
    filled in every packet.
    """

    state: Required[str]
    extension: Required[str]

    # IMU Data Packet Fields
    timestamp: int
    invalid_fields: list[str] | None

    # Raw Data Packet Fields
    scaledAccelX: str | None
    scaledAccelY: str | None
    scaledAccelZ: str | None
    scaledGyroX: str | None
    scaledGyroY: str | None
    scaledGyroZ: str | None
    deltaVelX: str | None
    deltaVelY: str | None
    deltaVelZ: str | None
    deltaThetaX: str | None
    deltaThetaY: str | None
    deltaThetaZ: str | None

    # Estimated Data Packet Fields
    estOrientQuaternionW: str | None
    estOrientQuaternionX: str | None
    estOrientQuaternionY: str | None
    estOrientQuaternionZ: str | None
    estPressureAlt: str | None
    estAttitudeUncertQuaternionW: str | None
    estAttitudeUncertQuaternionX: str | None
    estAttitudeUncertQuaternionY: str | None
    estAttitudeUncertQuaternionZ: str | None
    estAngularRateX: str | None
    estAngularRateY: str | None
    estAngularRateZ: str | None
    estCompensatedAccelX: str | None
    estCompensatedAccelY: str | None
    estCompensatedAccelZ: str | None
    estLinearAccelX: str | None
    estLinearAccelY: str | None
    estLinearAccelZ: str | None
    estGravityVectorX: str | None
    estGravityVectorY: str | None
    estGravityVectorZ: str | None

    # Processed Data Packet Fields
    current_altitude: str | None
    vertical_velocity: str | None
    vertical_acceleration: str | None

    # fields not in the data packets
    predicted_apogee: str | None
