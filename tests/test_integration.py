"""Integration coverage for a bounded replay of a real IMU launch CSV."""

import csv
import time
from pathlib import Path

import polars as pl

from airbrakes.context import Context
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_servo import MockServo


def test_bounded_real_imu_csv_replay_flows_through_context_and_logger(tmp_path, monkeypatch):
    """Replay actual recorded raw and estimated data without queuing the complete launch."""
    original_scan = MockIMU._scan_csv

    def bounded_scan(self, **kwargs):
        return original_scan(self, **kwargs).head(2_000)

    monkeypatch.setattr(MockIMU, "_scan_csv", bounded_scan)
    imu = MockIMU(
        real_time_replay=False,
        log_file_path=Path("launch_data/purple_launch.csv"),
        start_after_log_buffer=False,
    )
    logger = Logger(tmp_path)
    context = Context(MockServo(), imu, logger, DataProcessor(), ApogeePredictor())
    context.start(wait_for_start=True)

    while context.imu.is_running or context.imu.queued_imu_packets:
        context.update()
        time.sleep(0.001)
    context.stop()

    with logger.log_path.open(newline="") as log_file:
        rows = list(csv.DictReader(log_file))
    logged = pl.read_csv(logger.log_path)

    assert rows
    assert logged["state_letter"].drop_nulls().str.len_chars().eq(1).all()
    assert logged.filter(pl.col("scaledAccelX").is_not_null()).height > 0
    assert logged.filter(pl.col("estPressureAlt").is_not_null()).height > 0
    assert (
        logged.filter(pl.col("estPressureAlt").is_not_null())
        .select(pl.col("current_altitude").is_not_null().all())
        .item()
    )
    assert context.shutdown_requested
