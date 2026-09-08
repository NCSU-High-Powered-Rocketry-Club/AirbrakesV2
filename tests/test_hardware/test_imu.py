"""Tests for IMU hardware wrapper construction."""

import queue
import threading

from airbrakes.hardware.imu import IMU


def test_imu_initializes_packet_queue_and_fetch_thread():
    imu = IMU("/dev/ttyACM0")

    assert isinstance(imu._queued_imu_packets, queue.SimpleQueue)
    assert isinstance(imu._data_fetch_thread, threading.Thread)
    assert imu._data_fetch_thread.name == "IMU Thread"
    assert not imu.is_running
