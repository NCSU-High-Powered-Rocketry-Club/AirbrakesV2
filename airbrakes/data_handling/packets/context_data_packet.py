"""Module for the ContextPacket class."""

import msgspec


class ContextPacket(msgspec.Struct):
    """
    This data packet keeps data owned by the AirbrakesContext as well as metadata about the context.
    """

    update_timestamp: int
    """
    Our code often processes multiple packets at once, so this keeps track of the time at which the
    data was used to update the context.
    """
    state_name: str
    imu_queue_size: int
    data_processor_queue_size: int
    apogee_predictor_queue_size: int
