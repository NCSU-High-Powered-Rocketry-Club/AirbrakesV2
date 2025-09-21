"""
Module for the ContextDataPacket class.
"""

import msgspec

from airbrakes.state import State


class ContextDataPacket(msgspec.Struct, tag=True, array_like=True):
    """
    This data packet keeps data owned by the Context as well as metadata about the context.
    """

    state: type[State]
    """
    Represents the stage of flight we are in.

    This is the state that the state machine is in.
    """

    retrieved_imu_packets: int
    """
    This is the number of packets we got from the IMU process, in the main process.

    This number will always be below constants.MAX_FETCHED_PACKETS. If this number is on the high
    end, it indicates some performance issues with the main process.
    """

    queued_imu_packets: int
    """
    The number of IMU data packets in the IMU multiprocessing queue, waiting to be fetched, by the
    main process.
    """

    apogee_predictor_queue_size: int
    """
    The number of apogee predictor data packets in the apogee predictor queue, waiting to be fetched
    by the main process.
    """

    imu_packets_per_cycle: int
    """
    The number of packets we directly fetch from the LORD IMU in the IMU process.

    This is before we put the packets in the multiprocessing queue to the main process.
    """

    update_timestamp_ns: int
    """
    The timestamp reported by the local computer at which we processed and logged this data packet.

    This is used to compare the time difference between what is reported by the IMU, and when we
    finished processing the data packet.
    """
