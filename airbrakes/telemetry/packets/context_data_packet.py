"""Module for the ContextDataPacket class."""

from typing import Literal

import msgspec


class ContextDataPacket(msgspec.Struct):
    """
    This data packet keeps data owned by the AirbrakesContext as well as metadata about the context.
    """

    state_letter: Literal["S", "M", "C", "F", "L"]
    """Represents the stage of flight we are in. Will only be a single letter."""

    batch_number: int
    """
    Our code often processes multiple packets at once, so this keeps track of the current
    batch number. It is incremented every time a new batch of packets from the packet queue is
    processed.
    """

    imu_queue_size: int
    """
    The number of IMU data packets in the packet queue, waiting to be fetched, by the main
    process.
    """

    apogee_predictor_queue_size: int
    """
    The number of apogee predictor data packets in the apogee predictor queue,
    waiting to be fetched by the main process.
    """
