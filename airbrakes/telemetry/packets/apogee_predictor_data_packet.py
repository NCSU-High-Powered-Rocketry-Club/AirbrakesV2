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
    a_coefficient: float
    b_coefficient: float
    uncertainty_threshold_1: float
    uncertainty_threshold_2: float


class FirstApogeePredictionPacket(msgspec.Struct, tag=True, array_like=True):
    """
    Represents the first apogee prediction packet received after launch.

    This packet is only used by the display to show the initial apogee prediction.
    """

    predicted_apogee: float
    """
    The first predicted apogee we receive in coast state.
    """
    convergence_time: float
    """
    The number of seconds since we entered coast state when we received this packet.
    """
    convergence_height: float
    """
    The height at which we received this packet.
    """
