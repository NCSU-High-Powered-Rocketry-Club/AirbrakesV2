import multiprocessing
import multiprocessing.sharedctypes
import signal
import time
from collections import deque

import pytest

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket
from airbrakes.hardware.imu import IMU
from constants import FREQUENCY, PORT


class TestIMU:
    """Class to test the IMU class in imu.py"""

    def test_slots(self, imu):
        inst = imu
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, imu, mock_imu):
        """Tests whether the IMU and MockIMU objects initialize correctly."""
        # Tests that the data queue is correctly initialized
        assert isinstance(imu._data_queue, multiprocessing.queues.Queue)
        assert type(imu._data_queue) is type(mock_imu._data_queue)
        # Tests that _running is correctly initialized
        assert isinstance(imu._running, multiprocessing.sharedctypes.Synchronized)
        assert type(imu._running) is type(mock_imu._running)
        assert not imu._running.value
        assert not mock_imu._running.value
        # Tests that the process is correctly initialized
        assert isinstance(imu._data_fetch_process, multiprocessing.Process)
        assert type(imu._data_fetch_process) is type(mock_imu._data_fetch_process)

    def test_imu_start(self, monkeypatch):
        """Tests whether the IMU process starts correctly with the passed arguments."""
        values = multiprocessing.Queue()

        def _fetch_data_loop(self, port: str, frequency: int):
            """Monkeypatched method for testing."""
            print(port, frequency)
            values.put((port, frequency))

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=PORT, frequency=FREQUENCY)
        imu.start()
        assert imu._running.value
        assert imu.is_running
        assert imu._data_fetch_process.is_alive()
        time.sleep(0.01)  # Give the process time to start and put the values
        assert values.qsize() == 1
        assert values.get() == (PORT, FREQUENCY)

    def test_imu_stop(self, monkeypatch):
        """Tests whether the IMU process stops correctly."""

        def _fetch_data_loop(self, port: str, frequency: int):
            """Monkeypatched method for testing."""
            self._data_queue.put(EstimatedDataPacket(timestamp=0))

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=PORT, frequency=FREQUENCY)
        imu.start()
        time.sleep(0.01)  # Sleep a bit to let the process start and put the data
        assert imu._data_queue.qsize() == 1
        imu.stop()
        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        assert not imu._data_queue.qsize()

    def test_imu_ctrl_c_handling(self, monkeypatch):
        """Tests whether the IMU's stop() handles Ctrl+C fine."""
        values = multiprocessing.Queue(100000)

        def _fetch_data_loop(self, port: str, frequency: int):
            """Monkeypatched method for testing."""
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            while self._running.value:
                continue
            values.put((port, frequency))

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=PORT, frequency=FREQUENCY)
        imu.start()
        assert imu._running.value
        assert imu.is_running
        assert imu._data_fetch_process.is_alive()
        time.sleep(0.001)  # Give the process time to start and simulate the actual loop
        # send a KeyboardInterrupt to test if the process stops cleanly
        try:
            raise KeyboardInterrupt
        except KeyboardInterrupt:
            imu.stop()

        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        assert values.qsize() == 1
        assert values.get() == (PORT, FREQUENCY)

    def test_imu_fetch_loop_exception(self, monkeypatch):
        """Tests whether the IMU's _fetch_loop propogates unknown exceptions."""
        values = multiprocessing.Queue()

        def _fetch_data_loop(self, port: str, frequency: int):
            """Monkeypatched method for testing."""
            values.put((port, frequency))
            raise ValueError("some error")

        monkeypatch.setattr(IMU, "_fetch_data_loop", _fetch_data_loop)
        imu = IMU(port=PORT, frequency=FREQUENCY)
        imu.start()
        with pytest.raises(ValueError, match="some error") as excinfo:
            imu._fetch_data_loop(PORT, FREQUENCY)
        imu.stop()
        assert not imu._running.value
        assert not imu.is_running
        assert not imu._data_fetch_process.is_alive()
        assert values.qsize() == 2
        assert values.get() == (PORT, FREQUENCY)
        assert "some error" in str(excinfo.value)

    def test_data_packets_fetch(self, random_data_mock_imu):
        """Tests whether the data fetching loop actually adds data to the queue."""
        imu = random_data_mock_imu
        imu.start()
        time.sleep(0.3)
        # Theoretical number of packets in 0.3s:
        # 300ms / 2ms + 300ms / 1ms = 150 + 300 = 450
        assert imu._data_queue.qsize() > 400, "Queue should have more than 400 packets in 0.3s"
        assert isinstance(imu.get_imu_data_packet(), IMUDataPacket)

        # Get all the packets from the queue
        packets = imu.get_imu_data_packets()
        assert isinstance(packets, deque)
        assert isinstance(packets[0], IMUDataPacket)
        assert imu._data_queue.empty()
        imu.stop()

        # Assert ratio of EstimatedDataPackets to RawDataPackets is roughly 2:1:
        est_count = 0
        raw_count = 0
        for packet in packets:
            if isinstance(packet, EstimatedDataPacket):
                est_count += 1
            elif isinstance(packet, RawDataPacket):
                raw_count += 1

        # Practically the ratio may not be exactly 1:2
        assert 2.30 >= raw_count / est_count >= 1.70, f"Actual ratio was: {raw_count / est_count}"

    @pytest.mark.skip(reason="Need to install mscl in the CI and ideally auto-build locally.")
    def test_imu_data_loop(self):
        # Mock the MSCL library and related methods/classes to test the IMU data loop completely:
        pass
