"""Module for describing the data packet for the apogee predictor"""

import msgspec


class ApogeePredictorDataPacket(msgspec.Struct):
    """
    Represents a packet of data from the apogee predictor. This packet is used to communicate
    the apogee prediction and the uncertainty thresholds to the state machine.
    """
    predicted_apogee: float
    a_coefficient: float
    b_coefficient: float
    uncertainty_threshold_1: float
    uncertainty_threshold_2: float
