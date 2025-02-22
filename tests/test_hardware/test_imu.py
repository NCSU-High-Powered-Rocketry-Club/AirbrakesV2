import multiprocessing
import multiprocessing.sharedctypes
import signal
import time
from collections import deque
from ctypes import c_byte, c_int

import faster_fifo
import pytest

from airbrakes.constants import IMU_PORT
from airbrakes.hardware.imu import IMU
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from tests.auxil.utils import make_est_data_packet


class TestIMU:
    """Class to test the IMU class in imu.py"""

    def test_slots(self, imu):
        inst = imu
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, imu, mock_imu):
        """Tests whether the IMU and MockIMU objects initialize correctly."""
        # Tests that the data queue is correctly initialized
        assert isinstance(imu._queued_imu_packets, faster_fifo.Queue)
        assert type(imu._queued_imu_packets) is type(mock_imu._queued_imu_packets)
        # Tests that _running is correctly initialized
        assert isinstance(imu._running, c_byte)
        assert type(imu._running) is type(mock_imu._running)
        assert not imu._running.value
        assert not mock_imu._running.value
        # Tests that the process is correctly initialized
        assert isinstance(imu._data_fetch_process, multiprocessing.Process)
        assert type(imu._data_fetch_process) is type(mock_imu._data_fetch_process)

        # Test IMU properties:
        assert isinstance(imu.queued_imu_packets, int)
        assert isinstance(imu._imu_packets_per_cycle, c_int)
        assert isinstance(imu.imu_packets_per_cycle, int)

    def test_imu_start(self, monkeypatch):
        """Tests whether the IMU process starts correctly with the passed arguments."""
        values = faster_fifo.Queue()

        def _fetch_data_loop(self, port: str):
            """Monkeypatched method for testing."""
            values.put((port,))

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=IMU_PORT)
        imu.start()
        assert imu._running.value
        assert imu.is_running
        assert imu._data_fetch_process.is_alive()
        time.sleep(0.01)  # Give the process time to start and put the values
        assert values.qsize() == 1
        assert values.get() == (IMU_PORT,)

    def test_imu_stop_simple(self, monkeypatch):
        """Tests whether the IMU process stops correctly."""

        def _fetch_data_loop(self, port: str):
            """Monkeypatched method for testing."""
            self._queued_imu_packets.put(make_est_data_packet())

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.01)  # Sleep a bit to let the process start and put the data
        assert imu._queued_imu_packets.qsize() == 1
        imu.stop()
        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        # Tests that all packets were fetched while stopping:
        assert imu.queued_imu_packets == 0

    def test_imu_stop_when_queue_is_full(self, monkeypatch):
        """Tests whether the IMU process stops correctly when the queue is full."""
        monkeypatch.setattr("airbrakes.hardware.imu.MAX_QUEUE_SIZE", 10)

        def _fetch_data_loop(self, port: str):
            """Monkeypatched method for testing."""
            while self._running.value:
                self._queued_imu_packets.put(make_est_data_packet())

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.01)  # Sleep a bit to let the process start and put the data
        assert imu._queued_imu_packets.qsize() == 10
        imu.stop()
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        # Tests that all packets were fetched while stopping:
        # There is still one packet, since the process is stopped after the put()
        assert imu.queued_imu_packets == 1

    def test_imu_stop_signal(self, monkeypatch, mock_imu):
        """Tests that get_imu_data_packets() returns an empty deque upon receiving STOP_SIGNAL"""

        def _fetch_data_loop(self, port: str):
            """Monkeypatched method for testing."""
            # The stop_signal is typically put at the end of the mock sim.
            while self._running.value:
                self._queued_imu_packets.put(EstimatedDataPacket(timestamp=0))

        monkeypatch.setattr(mock_imu.__class__, "_fetch_data_loop", _fetch_data_loop)
        mock_imu.start()
        time.sleep(0.001)  # Give the process time to start and put the values
        packets = mock_imu.get_imu_data_packets()
        assert packets
        mock_imu.stop()  # puts STOP_SIGNAL in the queue
        packets = mock_imu.get_imu_data_packets()
        assert not packets, f"Expected empty deque, got {len(packets)} packets"

    def test_imu_ctrl_c_handling(self, monkeypatch):
        """Tests whether the IMU's stop() handles Ctrl+C fine."""
        values = faster_fifo.Queue(maxsize=100000)

        def _fetch_data_loop(self, port: str):
            """Monkeypatched method for testing."""
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            while self._running.value:
                continue
            values.put((port,))

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=IMU_PORT)
        imu.start()
        assert imu._running.value
        assert imu.is_running
        assert imu._data_fetch_process.is_alive()
        time.sleep(0.001)  # Give the process time to start and recreate the actual loop
        # send a KeyboardInterrupt to test if the process stops cleanly
        try:
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            imu.stop()

        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        assert values.qsize() == 1
        assert values.get() == (IMU_PORT,)

    def test_imu_fetch_loop_exception(self, monkeypatch):
        """Tests whether the IMU's _fetch_loop propogates unknown exceptions."""
        values = faster_fifo.Queue()

        def _fetch_data_loop(self, port: str):
            """Monkeypatched method for testing."""
            values.put((port,))
            raise ValueError("some error")

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(
            port=IMU_PORT,
        )
        imu.start()
        with pytest.raises(ValueError, match="some error") as excinfo:
            imu._fetch_data_loop(
                IMU_PORT,
            )
        imu.stop()
        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        assert values.qsize() == 2
        assert values.get() == (IMU_PORT,)
        assert "some error" in str(excinfo.value)

    def test_data_packets_fetch(self, random_data_mock_imu):
        """Tests whether the data fetching loop actually adds data to the queue."""
        imu = random_data_mock_imu
        imu.start()
        time.sleep(0.31)  # The raspberry pi is a little slower, so we add 0.01
        # Theoretical number of packets in 0.3s:
        # T = N / 1000 => N = 0.3 * 1000 = 300
        assert imu._queued_imu_packets.qsize() > 300, (
            "Queue should have more than 400 packets in 0.3s"
        )
        assert isinstance(imu.get_imu_data_packet(), IMUDataPacket)

        # Get all the packets from the queue
        packets = deque()
        imu.stop()
        while not imu._queued_imu_packets.empty():
            packets.extend(imu.get_imu_data_packets())

        assert isinstance(packets, deque)
        assert isinstance(packets[0], IMUDataPacket)
        assert imu._queued_imu_packets.empty()

        # Assert ratio of EstimatedDataPackets to RawDataPackets is roughly 2:1:
        est_count = 0
        raw_count = 0
        for packet in packets:
            if isinstance(packet, EstimatedDataPacket):
                est_count += 1
            elif isinstance(packet, RawDataPacket):
                raw_count += 1

        # Practically the ratio may not be exactly 1:1, specially on the raspberry pi
        assert 1.1 >= raw_count / est_count >= 0.95, f"Actual ratio was: {raw_count / est_count}"

    def test_imu_packet_fetch_timeout(self, monkeypatch, idle_mock_imu):
        """Tests whether the IMU's get_imu_data_packets() times out correctly."""
        imu = idle_mock_imu
        monkeypatch.setattr("airbrakes.interfaces.base_imu.IMU_TIMEOUT_SECONDS", 0.1)
        imu.start()
        packets = imu.get_imu_data_packets()
        assert not packets, "Expected empty deque"
        imu.stop()
