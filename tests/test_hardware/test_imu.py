"""Tests for IMU hardware packet conversion and lifecycle."""

import queue
import threading
import time

from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.hardware.imu import IMU


def test_imu_initializes_packet_queue_and_fetch_thread():
    imu = IMU("/dev/ttyACM0")

    assert isinstance(imu._queued_imu_packets, queue.SimpleQueue)
    assert isinstance(imu._data_fetch_thread, threading.Thread)
    assert imu._data_fetch_thread.name == "IMU Thread"
    assert not imu.is_running


def test_fetch_loop_converts_raw_and_estimated_parser_packets(monkeypatch):
    imu = IMU("/dev/ttyACM0")

    class RawParserPacket:
        packet_type = "raw"
        timestamp = 1
        invalid_fields = "raw-invalid"
        scaled_accel = (1.0, 2.0, 3.0)
        scaled_gyro = None
        delta_theta = (4.0, 5.0, 6.0)
        delta_vel = None
        scaled_ambient_pressure = 7.0

    class EstimatedParserPacket:
        packet_type = "estimated"
        timestamp = 2
        invalid_fields = None
        est_orient_quaternion = (1.0, 0.0, 0.0, 0.0)
        est_attitude_uncert_quaternion = None
        est_angular_rate = (8.0, 9.0, 10.0)
        est_compensated_accel = None
        est_linear_accel = (11.0, 12.0, 13.0)
        est_gravity_vector = None
        est_pressure_alt = 14.0

    class FakeParser:
        stopped = False

        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            pass

        def get_data_packets(self, *, block):
            assert block
            imu._requested_to_run.clear()
            return [RawParserPacket(), EstimatedParserPacket()]

        def stop(self):
            self.stopped = True

    monkeypatch.setattr("airbrakes.hardware.imu.mscl_rs.SerialParser", FakeParser)
    imu._requested_to_run.set()

    imu._fetch_data_loop("/dev/ttyACM0")
    raw_packet, estimated_packet = imu.get_imu_data_packets(block=False)

    assert imu.imu_packets_per_cycle == 2
    assert raw_packet == RawDataPacket(
        timestamp=1,
        invalid_fields="raw-invalid",
        scaledAccelX=1.0,
        scaledAccelY=2.0,
        scaledAccelZ=3.0,
        deltaThetaX=4.0,
        deltaThetaY=5.0,
        deltaThetaZ=6.0,
        scaledAmbientPressure=7.0,
    )
    assert estimated_packet == EstimatedDataPacket(
        timestamp=2,
        estOrientQuaternionW=1.0,
        estOrientQuaternionX=0.0,
        estOrientQuaternionY=0.0,
        estOrientQuaternionZ=0.0,
        estAngularRateX=8.0,
        estAngularRateY=9.0,
        estAngularRateZ=10.0,
        estLinearAccelX=11.0,
        estLinearAccelY=12.0,
        estLinearAccelZ=13.0,
        estPressureAlt=14.0,
    )


def test_stop_marker_does_not_discard_already_queued_imu_packets():
    packet = EstimatedDataPacket(timestamp=1)

    class QueuedPacketIMU(IMU):
        def _fetch_data_loop(self, _port):
            self._queued_imu_packets.put(packet)
            while self._requested_to_run.is_set():
                time.sleep(0.001)

    imu = QueuedPacketIMU("/dev/ttyACM0")
    imu.start()
    deadline = time.monotonic() + 1
    while imu.queued_imu_packets == 0 and time.monotonic() < deadline:
        time.sleep(0.001)

    imu.stop()

    assert imu.get_imu_data_packets(block=False) == [packet]
