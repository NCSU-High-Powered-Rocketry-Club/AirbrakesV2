"""Module for the ContextDataPacket class."""

from typing import Literal

import msgspec


class ContextDataPacket(msgspec.Struct, tag=True, array_like=True):
    """
    This data packet keeps data owned by the AirbrakesContext as well as metadata about the context.
    """

    state_letter: Literal["S", "M", "C", "F", "L"]
    """Represents the stage of flight we are in. Will only be a single letter."""

    fetched_packets_in_main: int
    """
    This is the number of packets from the IMU process, in the main process. This number will always
    be below constants.MAX_FETCHED_PACKETS. If this number is on the high end, it indicates some
    performance issues with the main process.
    """

    imu_queue_size: int
    """The number of IMU data packets in the IMU queue, waiting to be fetched, by the main
    process"""

    apogee_predictor_queue_size: int
    """The number of apogee predictor data packets in the apogee predictor queue,
    waiting to be fetched by the main process."""

    fetched_imu_packets: int
    """The number of packets we directly fetch from the LORD IMU in the IMU process. This is
    before we send the packets to the main process."""

    update_timestamp_ns: int
    """The timestamp reported by the local computer at which we processed
    and logged this data packet. This is used to compare the time difference between
    what is reported by the IMU, and when we finished processing the data packet."""
