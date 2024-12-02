"""Module for the DebugPacket class."""

import msgspec


class DebugPacket(msgspec.Struct):
    """Debug packet for logging miscellaneous debug information, such as queue sizes."""

    # All the fields below will only be added to the first packet being processed:
    # Curve coefficients for apogee prediction will only be added in the CoastState:
    predicted_apogee: float
    uncertainity_threshold_1: str
    uncertainity_threshold_2: str
    fetched_imu_packets: str
    packets_in_imu_queue: str
