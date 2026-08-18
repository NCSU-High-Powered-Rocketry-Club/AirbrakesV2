"""Module for describing the data packet for the apogee predictor."""

import msgspec


class ApogeePredictorDataPacket(msgspec.Struct, tag=True, array_like=True):
    """Represents a packet of data from the apogee predictor."""

    predicted_apogee: float
    """The predicted apogee of the rocket in meters."""

    height_used_for_prediction: float
    """The altitude used for the apogee prediction in meters."""

    vertical_velocity_meters_per_s_used_for_prediction: float
    """The vertical velocity used for the apogee prediction in meters per
    second."""

    horizontal_velocity_meters_per_s_used_for_prediction: float
    """The horizontal velocity used for the apogee prediction in meters per
    second."""

    tilt_angle_degrees_used_for_prediction: float
    """The tilt angle used for the apogee prediction in degrees."""

    angular_rate_deg_per_s_used_for_prediction: float
    """The angular rate used for the apogee prediction in degrees per
    second."""
