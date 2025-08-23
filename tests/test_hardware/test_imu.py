import multiprocessing
import multiprocessing.context
import multiprocessing.sharedctypes
import signal
import time
from collections import deque
from ctypes import c_byte, c_int

import faster_fifo

from airbrakes.constants import IMU_PORT
from airbrakes.hardware.imu import IMU
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from tests.auxil.utils import make_est_data_packet


class PortIMU(IMU):
    """
    IMU class that puts the port in the queue.
    """

    def _fetch_data_loop(self, port: str):
        self._running.value = True
        self._queued_imu_packets.put(port)
        self._running.value = False


class PacketsIMU(IMU):
    """
    IMU class that puts packets in the queue.
    """

    def _fetch_data_loop(self, _: str):
        self._running.value = True
        while self._requested_to_run.value:
            self._queued_imu_packets.put(make_est_data_packet())
        self._running.value = False


class SinglePacketIMU(IMU):
    """
    IMU class that only puts one packet in the queue.
    """

    def _fetch_data_loop(self, _: str):
        self._running.value = True
        self._queued_imu_packets.put(make_est_data_packet())
        self._running.value = False


class CtrlCIMU(IMU):
    """
    IMU class that handles Ctrl+C signals.
    """

    def _fetch_data_loop(self, port: str):
        """
        Monkeypatched method for testing.
        """
        self._running.value = True
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        while self._requested_to_run.value:
            continue
        self._queued_imu_packets.put(port)
        self._running.value = False


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
        assert isinstance(imu._queued_imu_packets, faster_fifo.Queue)
        assert type(imu._queued_imu_packets) is type(mock_imu._queued_imu_packets)
        # Tests that _running is correctly initialized
        assert isinstance(imu._running, c_byte)
        assert type(imu._running) is type(mock_imu._running)
        assert not imu._running.value
        assert not mock_imu._running.value
        # Tests that the process is correctly initialized
        assert isinstance(imu._data_fetch_process, multiprocessing.context.Process)
        assert type(imu._data_fetch_process) is type(mock_imu._data_fetch_process)

        # Test IMU properties:
        assert isinstance(imu.queued_imu_packets, int)
        assert isinstance(imu._imu_packets_per_cycle, c_int)
        assert isinstance(imu.imu_packets_per_cycle, int)

    def test_imu_start(self):
        """
        Tests whether the IMU process starts correctly with the passed arguments.
        """
        imu = PortIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.4)  # Give the process time to start and put the values
        assert imu._requested_to_run.value
        assert imu._queued_imu_packets.qsize() == 1
        assert imu._queued_imu_packets.get() == IMU_PORT

    def test_imu_stop_simple(self):
        """
        Tests whether the IMU process stops correctly.
        """
        imu = PortIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.2)  # Sleep a bit to let the process start and put the data
        assert imu._queued_imu_packets.qsize() == 1
        imu.stop()
        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        # Tests that all packets were fetched while stopping:
        assert imu.queued_imu_packets == 0

    def test_imu_stop_when_queue_is_full(self, monkeypatch):
        """
        Tests whether the IMU process stops correctly when the queue is full.
        """
        monkeypatch.setattr("airbrakes.hardware.imu.MAX_QUEUE_SIZE", 10)

        imu = PacketsIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.2)  # Sleep a bit to let the process start and put the data
        assert imu._queued_imu_packets.qsize() == 10
        imu.stop()
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        # Tests that all packets were fetched while stopping:
        # There is still one packet, since the process is stopped after the put()
        assert imu.queued_imu_packets == 1

    def test_imu_stop_signal(self):
        """
        Tests that get_imu_data_packets() returns an empty deque upon receiving STOP_SIGNAL.
        """
        imu = SinglePacketIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.01)  # Give the process time to start and put the values
        packets = imu.get_imu_data_packets()
        assert len(packets) == 1, f"Expected 1 packet, got {len(packets)} packets"
        imu.stop()  # puts STOP_SIGNAL in the queue
        packets = imu.get_imu_data_packets(block=False)
        assert not packets, f"Expected empty deque, got {len(packets)} packets"

    def test_imu_ctrl_c_handling(self):
        """
        Tests whether the IMU's stop() handles Ctrl+C fine.
        """
        imu = CtrlCIMU(port=IMU_PORT)
        imu.start()
        time.sleep(0.4)  # Give the process time to start and recreate the actual loop
        assert imu._running.value
        assert imu.is_running
        assert imu._data_fetch_process.is_alive()
        # send a KeyboardInterrupt to test if the process stops cleanly
        try:
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            imu.stop()

        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        assert imu._queued_imu_packets.qsize() == 1
        assert imu._queued_imu_packets.get() == IMU_PORT

    def test_data_packets_fetch(self, random_data_mock_imu):
        """
        Tests whether the data fetching loop actually adds data to the queue.
        """
        imu = random_data_mock_imu
        imu.start()
        time.sleep(0.7)  # Time to start the process
        time.sleep(0.31)  # Time to put data
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
        """
        Tests whether the IMU's get_imu_data_packets() times out correctly.
        """
        imu = idle_mock_imu
        monkeypatch.setattr("airbrakes.interfaces.base_imu.IMU_TIMEOUT_SECONDS", 0.1)
        imu.start()
        packets = imu.get_imu_data_packets()
        assert not packets, "Expected empty deque"
        imu.stop()
