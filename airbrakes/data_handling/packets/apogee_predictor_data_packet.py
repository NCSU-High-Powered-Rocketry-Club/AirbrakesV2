"""Module for describing the data packet for the apogee predictor."""

import msgspec


class ApogeePredictorDataPacket(msgspec.Struct, tag=True, array_like=True):
    """Represents a packet of data from the apogee predictor."""

    predicted_apogee: float
    """The predicted apogee of the rocket in meters."""

    height_used_for_prediction: float
    """The altitude used for the apogee prediction in meters."""

    velocity_used_for_prediction: float
    """The vertical velocity used for the apogee prediction in meters per
    second."""

    # TODO: implement once apogee prediction uses 3DOF
    # pitch_used_for_prediction: float
