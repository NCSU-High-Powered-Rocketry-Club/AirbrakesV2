"""Shared test fixtures."""

import queue
from pathlib import Path

import pytest

from airbrakes.context import Context
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_servo import MockServo

LOG_PATH = Path("tests/logs")
LAUNCH_DATA = list(Path("launch_data").glob("*.csv"))
LAUNCH_DATA_IDS = [log.stem for log in LAUNCH_DATA]


class IdleIMU:
    """Minimal IMU test double that remains running without producing packets."""

    def __init__(self) -> None:
        self._queue: queue.SimpleQueue = queue.SimpleQueue()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queued_imu_packets(self) -> int:
        return self._queue.qsize()

    @property
    def imu_packets_per_cycle(self) -> int:
        return 0

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def get_imu_data_packets(self, _block: bool = True) -> list:
        packets = []
        while not self._queue.empty():
            packets.append(self._queue.get())
        return packets


@pytest.fixture
def logger():
    """Clear test logs around each logger fixture."""
    for log in LOG_PATH.glob("log_*.csv"):
        log.unlink()
    instance = Logger(LOG_PATH)
    yield instance
    if instance.is_running:
        instance.stop()


@pytest.fixture
def data_processor():
    return DataProcessor()


@pytest.fixture
def servo():
    return MockServo()


@pytest.fixture
def apogee_predictor():
    return ApogeePredictor()


@pytest.fixture
def idle_imu():
    return IdleIMU()


@pytest.fixture
def context(idle_imu, logger, servo, data_processor, apogee_predictor):
    instance = Context(servo, idle_imu, logger, data_processor, apogee_predictor)
    yield instance
    if (
        instance.imu.is_running
        or instance.apogee_predictor.is_running
        or instance.logger.is_running
    ):
        instance.stop()


@pytest.fixture(params=LAUNCH_DATA, ids=LAUNCH_DATA_IDS)
def mock_imu(request):
    return MockIMU(log_file_path=request.param, real_time_replay=False, start_after_log_buffer=True)


@pytest.fixture
def mocked_args_parser():
    class MockArgs:
        mode = "mock"
        real_servo = False
        keep_log_file = False
        fast_replay = False
        debug = False
        path = None
        verbose = False

    return MockArgs()
