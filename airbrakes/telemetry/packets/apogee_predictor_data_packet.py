"""
Module for describing the data packet for the apogee predictor.
"""

import msgspec


class ApogeePredictorDataPacket(msgspec.Struct, tag=True, array_like=True):
    """
    Represents a packet of data from the apogee predictor.

    This packet is used to communicate the apogee prediction and the uncertainty thresholds to the
    state machine.
    """

    predicted_apogee: float
    """
    The predicted apogee of the rocket in meters.
    """

    a_coefficient: float
    """
    The 'a' coefficient used in the apogee prediction curve fit.
    """

    b_coefficient: float
    """
    The 'b' coefficient used in the apogee prediction curve fit.
    """

    uncertainty_threshold_1: float
    """
    The first uncertainty threshold for apogee prediction in meters.
    """

    uncertainty_threshold_2: float
    """
    The second uncertainty threshold for apogee prediction in meters.
    """
