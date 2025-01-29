"""Module for the ContextDataPacket class."""

from typing import Literal

import msgspec


class ContextDataPacket(msgspec.Struct, tag=True, array_like=True):
    """
    This data packet keeps data owned by the AirbrakesContext as well as metadata about the context.
    """

    state_letter: Literal["S", "M", "C", "F", "L"]
    """Represents the stage of flight we are in. Will only be a single letter."""

    batch_number: int
    """
    Our code often processes multiple packets at once, so this keeps track of the current
    batch number. It is incremented every time a new batch of packets is processed. This is the
    number of times airbrakes.update() was called.
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
