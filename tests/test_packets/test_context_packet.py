"""Tests for IMU context packets."""

import pytest

from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.state import StandbyState


def test_context_packet_records_imu_metrics():
    packet = ContextDataPacket(
        state=StandbyState,
        retrieved_imu_packets=2,
        queued_imu_packets=3,
        imu_packets_per_cycle=4,
        apogee_predictor_queue_size=5,
        update_timestamp_ns=6,
    )
    assert packet.retrieved_imu_packets == 2
    assert packet.queued_imu_packets == 3
    assert packet.imu_packets_per_cycle == 4


def test_context_packet_requires_all_metrics():
    with pytest.raises(TypeError):
        ContextDataPacket()
