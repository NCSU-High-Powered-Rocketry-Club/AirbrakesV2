"""Data produced by the coordinating flight context."""

import msgspec


class ContextDataPacket(msgspec.Struct, array_like=True, kw_only=True):
    """Context state and IMU queue observability for a log row."""

    state: type
    retrieved_imu_packets: int
    queued_imu_packets: int
    imu_packets_per_cycle: int
    apogee_predictor_queue_size: int
    update_timestamp_ns: int
