"""Data packet schemas for raw and estimated measurements from the IMU."""

import msgspec


class IMUDataPacket(msgspec.Struct, array_like=True, tag=True):
    """
    Base class for data packets received from the IMU.

    The attribute names intentionally match the camelCase field names sent by the IMU. Individual
    measurements are optional because the IMU may omit a field or report it as invalid.
    """

    timestamp: int
    """
    The IMU timestamp for this packet, in nanoseconds since the Unix epoch.
    """

    invalid_fields: str | None = None
    """
    A comma-separated list of IMU fields that may be invalid.

    This value is reported by the IMU. A field named here should not be treated as a reliable
    measurement, even if a numeric value is present.
    """


class RawDataPacket(IMUDataPacket):
    """
    Represents a raw measurement packet from the IMU.

    These values are the IMU's direct output and have not been processed by the flight software. The
    packet contains acceleration, angular-rate, delta-velocity, delta-angle, and ambient-pressure
    measurements. A component is ``None`` when the IMU did not provide it.
    """

    scaledAccelX: float | None = None
    """Specific-force measurement along the IMU X axis, in g (standard gravity)."""
    scaledAccelY: float | None = None
    """Specific-force measurement along the IMU Y axis, in g (standard gravity)."""
    scaledAccelZ: float | None = None  # this will be ~-1.0g when the IMU is at rest
    """Specific-force measurement along the IMU Z axis, in g (standard gravity)."""

    scaledGyroX: float | None = None
    """Angular-rate measurement about the IMU X axis, in radians per second."""
    scaledGyroY: float | None = None
    """Angular-rate measurement about the IMU Y axis, in radians per second."""
    scaledGyroZ: float | None = None
    """Angular-rate measurement about the IMU Z axis, in radians per second."""

    deltaVelX: float | None = None
    """Integrated specific force along the IMU X axis, in g seconds."""
    deltaVelY: float | None = None
    """Integrated specific force along the IMU Y axis, in g seconds."""
    deltaVelZ: float | None = None
    """Integrated specific force along the IMU Z axis, in g seconds."""

    deltaThetaX: float | None = None
    """Incremental rotation about the IMU X axis during the sample, in radians."""
    deltaThetaY: float | None = None
    """Incremental rotation about the IMU Y axis during the sample, in radians."""
    deltaThetaZ: float | None = None
    """Incremental rotation about the IMU Z axis during the sample, in radians."""

    scaledAmbientPressure: float | None = None
    """Ambient atmospheric pressure measured by the IMU, in millibars."""


class EstimatedDataPacket(IMUDataPacket):
    """
    Represents an estimated measurement packet from the IMU.

    These values are processed and filtered internally by the IMU from its raw sensor measurements.
    They include pressure altitude, orientation, attitude uncertainty, angular rate, acceleration,
    and gravity estimates. A component is ``None`` when the IMU did not provide it.
    """

    estPressureAlt: float | None = None
    """The estimated pressure altitude in meters."""

    estOrientQuaternionW: float | None = None
    """The W (scalar) component of the estimated orientation quaternion."""
    estOrientQuaternionX: float | None = None
    """The X component of the estimated orientation quaternion."""
    estOrientQuaternionY: float | None = None
    """The Y component of the estimated orientation quaternion."""
    estOrientQuaternionZ: float | None = None
    """The Z component of the estimated orientation quaternion."""

    estAttitudeUncertQuaternionW: float | None = None
    """The W (scalar) component of the estimated attitude uncertainty quaternion."""
    estAttitudeUncertQuaternionX: float | None = None
    """The X component of the estimated attitude uncertainty quaternion."""
    estAttitudeUncertQuaternionY: float | None = None
    """The Y component of the estimated attitude uncertainty quaternion."""
    estAttitudeUncertQuaternionZ: float | None = None
    """The Z component of the estimated attitude uncertainty quaternion."""

    estAngularRateX: float | None = None
    """The estimated angular rate about the IMU X axis, in radians per second."""
    estAngularRateY: float | None = None
    """The estimated angular rate about the IMU Y axis, in radians per second."""
    estAngularRateZ: float | None = None
    """The estimated angular rate about the IMU Z axis, in radians per second."""

    estCompensatedAccelX: float | None = None
    """The estimated acceleration along the IMU X axis, in meters per second squared, including
    gravity."""
    estCompensatedAccelY: float | None = None
    """The estimated acceleration along the IMU Y axis, in meters per second squared, including
    gravity."""
    estCompensatedAccelZ: float | None = None  # this will be ~-9.81 m/s^2 when the IMU is at rest
    """The estimated acceleration along the IMU Z axis, in meters per second squared, including
    gravity."""

    estLinearAccelX: float | None = None
    """The estimated linear acceleration along the IMU X axis, in meters per second squared, with
    gravity removed."""
    estLinearAccelY: float | None = None
    """The estimated linear acceleration along the IMU Y axis, in meters per second squared, with
    gravity removed."""
    estLinearAccelZ: float | None = None  # this will be ~0 m/s^2 when the IMU is at rest
    """The estimated linear acceleration along the IMU Z axis, in meters per second squared, with
    gravity removed."""

    estGravityVectorX: float | None = None
    """The estimated gravity vector's X component, in meters per second squared."""
    estGravityVectorY: float | None = None
    """The estimated gravity vector's Y component, in meters per second squared."""
    estGravityVectorZ: float | None = None
    """The estimated gravity vector's Z component, in meters per second squared."""
