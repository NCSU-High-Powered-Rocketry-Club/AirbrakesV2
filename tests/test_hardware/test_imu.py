import queue
import signal
import threading
import time
from pathlib import Path

import pytest

from airbrakes.constants import IMU_PORT
from airbrakes.data_handling.packets.imu_data_packet import (
    IMUDataPacket,
)
from airbrakes.hardware.imu import IMU
from airbrakes.mock.mock_imu import MockIMU
from tests.auxil.utils import make_est_data_packet


class PortIMU(IMU):
    """
    IMU class that puts the port in the queue.
    """

    def _fetch_data_loop(self, port: str):
        self._running.set()
        self._queued_imu_packets.put(port)
        self._running.clear()


class PacketsIMU(IMU):
    """
    IMU class that puts packets in the queue.
    """

    def _fetch_data_loop(self, _: str):
        self._running.set()
        while self._requested_to_run.is_set():
            self._queued_imu_packets.put(make_est_data_packet())
        self._running.clear()


class SinglePacketIMU(IMU):
    """
    IMU class that only puts one packet in the queue.
    """

    def _fetch_data_loop(self, _: str):
        self._running.set()
        self._queued_imu_packets.put(make_est_data_packet())
        self._running.clear()


class CtrlCIMU(IMU):
    """
    IMU class that handles Ctrl+C signals.
    """

    def _fetch_data_loop(self, port: str):
        """
        Monkeypatched method for testing.
        """
        self._running.set()
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while self._requested_to_run.is_set():
            continue
        self._queued_imu_packets.put(port)
        self._running.clear()


class TestIMU:
    """
    Class to test the IMU class in imu.py.
    """

    def test_slots(self, imu):
        inst = imu
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, imu, mock_imu):
        """
        Tests whether the IMU and MockIMU objects initialize correctly.
        """
        # Tests that the data queue is correctly initialized
        assert isinstance(imu._queued_imu_packets, queue.SimpleQueue)
        assert type(imu._queued_imu_packets) is type(mock_imu._queued_imu_packets)
        # Tests that _running is correctly initialized
        assert isinstance(imu._running, threading.Event)
        assert type(imu._running) is type(mock_imu._running)
        assert not imu._running.is_set()
        assert not mock_imu._running.is_set()
        # Tests that the thread is correctly initialized
        assert isinstance(imu._data_fetch_thread, threading.Thread)
        assert type(imu._data_fetch_thread) is type(mock_imu._data_fetch_thread)

        # Test IMU properties:
        assert isinstance(imu.queued_imu_packets, int)
        assert isinstance(imu._imu_packets_per_cycle, int)
        assert isinstance(imu.imu_packets_per_cycle, int)

        # Test Legacy Launch 2 exception:
        with pytest.raises(ValueError, match="There is no data for this flight"):
            MockIMU(False, log_file_path=Path("launch_data/legacy_launch_2.csv"))

    def test_imu_start(self):
        """
        Tests whether the IMU thread starts correctly with the passed arguments.
        """
        imu = PortIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.4)  # Give the thread time to start and put the values
        assert imu._requested_to_run.is_set()
        assert imu._queued_imu_packets.qsize() == 1
        assert imu._queued_imu_packets.get() == IMU_PORT

    def test_imu_stop_simple(self):
        """
        Tests whether the IMU thread stops correctly.
        """
        imu = PortIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.4)  # Sleep a bit to let the thread start and put the data
        assert imu._queued_imu_packets.qsize() == 1
        imu.stop()
        assert not imu._running.is_set()
        assert not imu.is_running
        assert not imu._data_fetch_thread.is_alive()
        # Test that packets are waiting in the queue before stopping (including the STOP_SIGNAL):
        assert imu.queued_imu_packets == 2

    def test_imu_stop_when_queue_is_full(self):
        """
        Tests whether the IMU thread stops correctly when the queue is full.
        """
        imu = PacketsIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.2)  # Sleep a bit to let the thread start and put the data
        assert imu._queued_imu_packets.qsize() >= 10
        imu.stop()
        assert not imu.is_running
        assert not imu._data_fetch_thread.is_alive()
        assert imu.queued_imu_packets > 1000

    def test_imu_stop_signal(self):
        """
        Tests that get_imu_data_packets() returns an empty deque upon receiving STOP_SIGNAL.
        """
        imu = SinglePacketIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.01)  # Give the thread time to start and put the values
        packets = imu.get_imu_data_packets()
        assert len(packets) == 1, f"Expected 1 packet, got {len(packets)} packets"
        imu.stop()  # puts STOP_SIGNAL in the queue
        packets = imu.get_imu_data_packets(block=False)
        assert not packets, f"Expected empty deque, got {len(packets)} packets"

    def test_data_packets_fetch(self, random_data_mock_imu):
        """
        Tests whether the data fetching loop actually adds data to the queue.
        """
        imu = random_data_mock_imu
        imu.start()
        time.sleep(0.9)  # Time to start the thread
        time.sleep(0.31)  # Time to put data
        # Theoretical number of packets in 0.3s:
        # T = N / 1000 => N = 0.3 * 1000 = 300
        assert imu._queued_imu_packets.qsize() > 300, (
            "Queue should have more than 400 packets in 0.3s"
        )
        assert isinstance(imu.get_imu_data_packet(), IMUDataPacket)
        imu.stop()
