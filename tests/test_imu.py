import multiprocessing
import multiprocessing.sharedctypes
import time
from collections import deque

import pytest

from airbrakes.constants import FREQUENCY, PORT, UPSIDE_DOWN
from airbrakes.imu.imu import IMU
from airbrakes.imu.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket


@pytest.fixture
def imu():
    return IMU(port=PORT, frequency=FREQUENCY, upside_down=UPSIDE_DOWN)


RAW_DATA_PACKET_SAMPLING_RATE = 1 / 1000  # 1kHz
EST_DATA_PACKET_SAMPLING_RATE = 1 / 500  # 500Hz


class TestIMU:
    """Class to test the IMU class in imu.py"""

    def test_init(self, imu):
        assert isinstance(imu._data_queue, multiprocessing.queues.Queue)
        # Test that _running is a shared boolean multiprocessing.Value:
        assert isinstance(imu._running, multiprocessing.sharedctypes.Synchronized)
        assert isinstance(imu._data_fetch_process, multiprocessing.Process)

    def test_imu_start(self, monkeypatch):
        """Tests whether the IMU process starts correctly with the passed arguments."""
        values = multiprocessing.Queue()

        def _fetch_data_loop(self, port: str, frequency: int, upside_down: bool):
            """Monkeypatched method for testing."""
            values.put((port, frequency, upside_down))

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=PORT, frequency=FREQUENCY, upside_down=UPSIDE_DOWN)
        imu.start()
        assert imu._running.value
        assert imu.is_running
        assert imu._data_fetch_process.is_alive()
        time.sleep(0.01)  # Give the process time to start and put the values
        assert values.qsize() == 1
        assert values.get() == (PORT, FREQUENCY, UPSIDE_DOWN)

    def test_imu_stop(self, monkeypatch):
        """Tests whether the IMU process stops correctly."""

        def _fetch_data_loop(self, port: str, frequency: int, upside_down: bool):
            """Monkeypatched method for testing."""

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=PORT, frequency=FREQUENCY, upside_down=UPSIDE_DOWN)
        imu.start()
        imu.stop()
        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()

    def test_data_packets_fetch(self, monkeypatch):
        """Tests whether the data fetching loop actually adds data to the queue."""

        def _fetch_data_loop(self, *_, **__):
            """Monkeypatched method for testing.
            We can't simulate the actual IMU without the hardware.
            So we simulate the data fetching loop at the correct sampling rate instead.
            """
            next_estimated_packet_time = time.time()
            next_raw_packet_time = time.time()

            while self._running.value:
                current_time = time.time()
                # Generate dummy packets, 1 EstimatedDataPacket every 500Hz, and 1 RawDataPacket
                # every 1000Hz
                # sleep for the time it would take to get the next packet
                if current_time >= next_estimated_packet_time:
                    estimated_packet = EstimatedDataPacket(timestamp=123456789)
                    self._data_queue.put(estimated_packet)
                    next_estimated_packet_time += EST_DATA_PACKET_SAMPLING_RATE

                if current_time >= next_raw_packet_time:
                    raw_packet = RawDataPacket(timestamp=987654321)
                    self._data_queue.put(raw_packet)
                    next_raw_packet_time += RAW_DATA_PACKET_SAMPLING_RATE

                # Sleep a little to prevent busy-waiting
                time.sleep(0.001)

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=PORT, frequency=FREQUENCY, upside_down=UPSIDE_DOWN)
        imu.start()
        time.sleep(0.3)
        imu.stop()
        # Theoretical number of packets in 0.3s:
        # 300ms / 2ms + 300ms / 1ms = 150 + 300 = 450
        assert imu._data_queue.qsize() > 400, "Queue should have more than 400 packets in 0.3s"
        assert isinstance(imu.get_imu_data_packet(), IMUDataPacket)

        # Get all the packets from the queue
        packets = imu.get_imu_data_packets()
        assert isinstance(packets, deque)
        assert isinstance(packets[0], IMUDataPacket)
        assert imu._data_queue.empty()

        # Assert ratio of EstimatedDataPackets to RawDataPackets is roughly 2:1:
        est_count = 0
        raw_count = 0
        for packet in packets:
            if isinstance(packet, EstimatedDataPacket):
                est_count += 1
            elif isinstance(packet, RawDataPacket):
                raw_count += 1

        # Practically the ratio may not be exactly 1:2
        assert raw_count / est_count >= 1.70, f"Actual ratio was: {raw_count / est_count}"
