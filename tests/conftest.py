"""
Module where fixtures are shared between all test files.
"""

import multiprocessing
import time
from pathlib import Path

import pytest

from airbrakes.constants import (
    ENCODER_PIN_A,
    ENCODER_PIN_B,
    EST_DATA_PACKET_SAMPLING_RATE,
    IMU_PORT,
    RAW_DATA_PACKET_SAMPLING_RATE,
    SERVO_CHANNEL,
)
from airbrakes.context import Context
from airbrakes.hardware.imu import IMU
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_servo import MockServo
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.telemetry.logger import Logger
from tests.auxil.utils import make_est_data_packet, make_raw_data_packet

LOG_PATH = Path("tests/logs")
# Get all csv files in the launch_data directory:
LAUNCH_DATA = list(Path("launch_data").glob("*.csv"))
# Remove the genesis_launch_1.csv file since it's almost the same as genesis_launch_2.csv:
LAUNCH_DATA.remove(Path("launch_data/genesis_launch_1.csv"))
# Remove the legacy_launch_2.csv file since it failed
LAUNCH_DATA.remove(Path("launch_data/legacy_launch_2.csv"))
# Use the filenames as the ids for the fixtures:
LAUNCH_DATA_IDS = [log.stem for log in LAUNCH_DATA]

multiprocessing.set_start_method("spawn", force=True)


def pytest_collection_modifyitems(config, items):
    marker = "imu_benchmark"
    marker_expr = config.getoption("-m", None)

    # Skip tests with the marker if not explicitly requested
    if marker_expr != marker:
        skip_marker = pytest.mark.skip(reason=f"Test requires '-m {marker}'")
        for item in items:
            if item.get_closest_marker(marker):
                item.add_marker(skip_marker)


@pytest.fixture
def logger():
    """
    Clear the tests/logs directory before making a new Logger.
    """
    for log in LOG_PATH.glob("log_*.csv"):
        log.unlink()
    logger = Logger(LOG_PATH)
    yield logger
    if logger.is_running:
        logger.stop()


@pytest.fixture
def data_processor():
    return DataProcessor()


@pytest.fixture
def imu():
    imu = IMU(port=IMU_PORT)
    yield imu
    if imu.is_running:
        imu.stop()


@pytest.fixture
def servo():
    return MockServo(SERVO_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)


@pytest.fixture
def apogee_predictor():
    return ApogeePredictor()


@pytest.fixture
def context(imu, logger, servo, data_processor, apogee_predictor):
    ab = Context(servo, imu, logger, data_processor, apogee_predictor)
    yield ab
    # Check if something is running:
    if ab.imu.is_running or ab.apogee_predictor.is_running or ab.logger.is_running:
        ab.stop()  # Helps cleanup failing tests that don't stop the airbrakes context


@pytest.fixture
def mock_imu_airbrakes(mock_imu, logger, servo, data_processor, apogee_predictor):
    """
    Fixture that returns an Context object with a mock IMU.

    This will run for all the launch data files (see the mock_imu fixture)
    """
    ab = Context(servo, mock_imu, logger, data_processor, apogee_predictor)
    yield ab
    # Check if something is running:
    if ab.imu.is_running or ab.apogee_predictor.is_running or ab.logger.is_running:
        ab.stop()


@pytest.fixture
def random_data_mock_imu():
    # A mock IMU that outputs random data packets
    imu = RandomDataIMU(port=IMU_PORT)
    yield imu
    if imu.is_running:
        imu.stop()


@pytest.fixture
def idle_mock_imu():
    # A sleeping IMU that doesn't output any data packets
    imu = IdleIMU(port=IMU_PORT)
    yield imu
    if imu.is_running:
        imu.stop()


@pytest.fixture(params=LAUNCH_DATA, ids=LAUNCH_DATA_IDS)
def mock_imu(request):
    """
    Fixture that returns a MockIMU object with the specified log file.
    """
    return MockIMU(log_file_path=request.param, real_time_replay=False, start_after_log_buffer=True)


@pytest.fixture
def mocked_args_parser():
    """
    Fixture that returns a mocked argument parser.
    """

    class MockArgs:
        mode = "mock"
        real_servo = False
        keep_log_file = False
        fast_replay = False
        debug = False
        path = None
        verbose = False
        sim = False
        real_imu = False

    return MockArgs()


@pytest.fixture
def target_altitude(request):
    """
    Fixture to return the target altitude based on the mock IMU log file name.
    """
    # This will be used to set the constants for the test, since they change for different flights:
    # request.node.name is the name of the test function, e.g. test_update[shake_n_bake]
    launch_name = request.node.name.split("[")[-1].strip("]")
    # We set the target altitude about 50m less than its actual value, since we want to test
    # that the airbrakes deploy before it hits its true apogee.
    if launch_name == "purple_launch":
        return 750.0  # actual apogee was about 794m
    if launch_name == "shake_n_bake":
        return 1800.0  # actual apogee was about 1854m
    if launch_name == "genesis_launch_2":
        return 413.0  # actual apogee was about 462m
    if launch_name == "legacy_launch_1":
        return 580.0  # actual apogee was about 631.14m
    # Airbrakes actually deployed on this flight, and we had set an apogee higher than the actual
    # apogee achieved because of the airbrakes.
    if launch_name == "pelicanator_launch_1":
        return 1218.9  # actual apogee was about 1208.9m
    if launch_name == "pelicanator_launch_2":
        return 1127.76  # actual apogee was about 1090.16m
    # Airbrakes actually deployed on this flight-
    if launch_name == "pelicanator_launch_3":
        return 1110.6  # actual apogee was about 1160.6m
    if launch_name == "pelicanator_launch_4":
        return 1200.0  # actual apogee was about TBD
    return 1000.0  # Default altitude


class RandomDataIMU(IMU):
    """
    Mocks the data fetch loop, since we don't have the actual IMU to use locally.
    """

    __slots__ = ()

    def _fetch_data_loop(self, _: str) -> None:
        """
        Output Est and Raw Data packets at the sampling rate we use for the IMU.
        """
        self._running.value = True
        # Convert sampling rates to nanoseconds: 1/500Hz = 2ms = 2000000 ns, 1/1000Hz = 1000000 ns
        EST_INTERVAL_NS = int(EST_DATA_PACKET_SAMPLING_RATE * 1e9)
        RAW_INTERVAL_NS = int(RAW_DATA_PACKET_SAMPLING_RATE * 1e9)

        # Initialize next packet times with first interval
        next_estimated = time.time_ns() + EST_INTERVAL_NS
        next_raw = time.time_ns() + RAW_INTERVAL_NS

        while self._requested_to_run.value:
            now = time.time_ns()

            # Generate all raw packets due since last iteration
            while now >= next_raw:
                self._queued_imu_packets.put(make_raw_data_packet(timestamp=next_raw))
                next_raw += RAW_INTERVAL_NS

            # Generate all estimated packets due since last iteration
            while now >= next_estimated:
                self._queued_imu_packets.put(make_est_data_packet(timestamp=next_estimated))
                next_estimated += EST_INTERVAL_NS

            # Calculate sleep time until next expected packet
            next_event = min(next_raw, next_estimated)
            sleep_time = (next_event - time.time_ns()) / 1e9  # Convert ns to seconds

            # Only sleep if we're ahead of schedule
            if sleep_time > 0.0001:  # 100μs buffer for precision
                time.sleep(sleep_time * 0.5)  # Sleep half the interval to maintain timing
        self._running.value = False


class IdleIMU(IMU):
    """
    Mocks the IMU data fetch loop, but doesn't output any data packets.
    """

    def _fetch_data_loop(self, _: str) -> None:
        while self.requested_to_run:
            time.sleep(0.1)
