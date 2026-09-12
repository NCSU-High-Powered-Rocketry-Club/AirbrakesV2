"""Regression tests for IMU log construction, buffering, and lifecycle."""

import csv
import time

import pytest

from airbrakes.constants import IDLE_LOG_CAPACITY, LOG_BUFFER_SIZE
from airbrakes.data_handling.logger import Logger
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.state import LandedState, MotorBurnState, StandbyState
from tests.auxil.utils import (
    make_context_data_packet,
    make_est_data_packet,
    make_processor_data_packet,
    make_raw_data_packet,
    make_servo_data_packet,
)


def _read_rows(log_path):
    with log_path.open(newline="") as log_file:
        return list(csv.DictReader(log_file))


class TestLogger:
    """Verify all IMU rows remain aligned through asynchronous logging."""

    def test_initializes_numbered_file_with_complete_headers(self, logger):
        second_logger = Logger(logger.log_path.parent)

        assert logger.log_path.name == "log_1.csv"
        assert second_logger.log_path.name == "log_2.csv"
        assert _read_rows(logger.log_path) == []
        with logger.log_path.open(newline="") as log_file:
            assert csv.DictReader(log_file).fieldnames == list(LoggerDataPacket.__struct_fields__)

    def test_prepare_rows_preserves_raw_estimated_order_and_alignment(self):
        raw_packet = make_raw_data_packet(timestamp=1, scaledAccelX=1.0)
        estimated_packet = make_est_data_packet(timestamp=2, estPressureAlt=100.0)
        processed_packet = make_processor_data_packet(current_altitude=5.0)

        rows = Logger._prepare_logger_packets(
            make_context_data_packet(state=StandbyState),
            make_servo_data_packet(),
            [raw_packet, estimated_packet],
            [processed_packet],
            None,
        )

        assert [row.timestamp for row in rows] == [1, 2]
        assert rows[0].scaledAccelX == 1.0
        assert rows[0].current_altitude is None
        assert rows[1].estPressureAlt == 100.0
        assert rows[1].current_altitude == 5.0

    @pytest.mark.parametrize(
        ("imu_packets", "processor_packets"),
        [
            ([make_raw_data_packet()], [make_processor_data_packet()]),
            ([make_est_data_packet()], []),
            ([make_raw_data_packet(), make_est_data_packet()], []),
        ],
    )
    def test_prepare_rows_rejects_unaligned_processor_packets(self, imu_packets, processor_packets):
        with pytest.raises(ValueError, match="align"):
            Logger._prepare_logger_packets(
                make_context_data_packet(state=StandbyState),
                make_servo_data_packet(),
                imu_packets,
                processor_packets,
                None,
            )

    def test_stop_flushes_buffered_standby_rows(self, logger):
        logger.start()
        logger.log(
            make_context_data_packet(state=StandbyState),
            make_servo_data_packet(),
            [make_raw_data_packet(timestamp=index) for index in range(IDLE_LOG_CAPACITY + 3)],
            [],
            None,
        )

        assert len(logger._log_buffer) == 3
        logger.stop()

        assert not logger.is_running
        assert not logger._log_buffer
        assert len(_read_rows(logger.log_path)) == IDLE_LOG_CAPACITY + 3

    def test_idle_buffer_is_capacity_limited(self, logger):
        logger.start()
        logger.log(
            make_context_data_packet(state=StandbyState),
            make_servo_data_packet(),
            [
                make_raw_data_packet(timestamp=index)
                for index in range(IDLE_LOG_CAPACITY + LOG_BUFFER_SIZE + 25)
            ],
            [],
            None,
        )

        assert logger.is_log_buffer_full
        assert len(logger._log_buffer) == LOG_BUFFER_SIZE
        logger.stop()
        assert len(_read_rows(logger.log_path)) == IDLE_LOG_CAPACITY + LOG_BUFFER_SIZE

    def test_transition_from_standby_flushes_buffer_before_active_rows(self, logger):
        standby = make_context_data_packet(state=StandbyState)
        motor_burn = make_context_data_packet(state=MotorBurnState)
        servo = make_servo_data_packet()
        logger.start()
        logger.log(
            standby,
            servo,
            [make_raw_data_packet(timestamp=index) for index in range(IDLE_LOG_CAPACITY + 2)],
            [],
            None,
        )
        logger.log(motor_burn, servo, [make_raw_data_packet(timestamp=999)], [], None)
        logger.stop()

        rows = _read_rows(logger.log_path)
        assert len(rows) == IDLE_LOG_CAPACITY + 3
        assert [row["state_letter"] for row in rows[-3:]] == ["S", "S", "M"]

    def test_landed_rows_follow_the_same_capacity_and_flush_lifecycle(self, logger):
        logger.start()
        logger.log(
            make_context_data_packet(state=LandedState),
            make_servo_data_packet(),
            [make_raw_data_packet(timestamp=index) for index in range(IDLE_LOG_CAPACITY + 2)],
            [],
            None,
        )
        logger.stop()

        rows = _read_rows(logger.log_path)
        assert len(rows) == IDLE_LOG_CAPACITY + 2
        assert {row["state_letter"] for row in rows} == {"L"}

    def test_logging_thread_accepts_rows_and_stops_on_stop_signal(self, logger):
        logger.start()
        logger._log_queue.put(
            LoggerDataPacket(
                state_letter="S",
                current_position=0.0,
                timestamp=42,
            )
        )
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline and not _read_rows(logger.log_path):
            time.sleep(0.01)
        logger.stop()

        rows = _read_rows(logger.log_path)
        assert len(rows) == 1
        assert rows[0]["timestamp"] == "42"
