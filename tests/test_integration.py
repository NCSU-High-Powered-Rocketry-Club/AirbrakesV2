"""Integration test for the restored IMU CSV replay path."""

import time
from pathlib import Path

from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.mock.mock_imu import MockIMU


def test_mock_imu_replays_raw_and_estimated_packets():
    imu = MockIMU(
        real_time_replay=False,
        log_file_path=Path("launch_data/purple_launch.csv"),
        start_after_log_buffer=False,
    )
    imu.start()
    deadline = time.monotonic() + 5
    packets = []
    while time.monotonic() < deadline and len(packets) < 100:
        packets.extend(imu.get_imu_data_packets(block=False))
        if not imu.is_running:
            break
        time.sleep(0.01)
    imu.stop()

    assert packets
    assert any(isinstance(packet, RawDataPacket) for packet in packets)
    assert any(isinstance(packet, EstimatedDataPacket) for packet in packets)
