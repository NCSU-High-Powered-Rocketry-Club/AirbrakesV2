"""Module where fixtures are shared between all test files."""

import time
from pathlib import Path

import pytest
from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.constants import (
    EST_DATA_PACKET_SAMPLING_RATE,
    IMU_PORT,
    RAW_DATA_PACKET_SAMPLING_RATE,
    SERVO_PIN,
)
from airbrakes.hardware.camera import Camera
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_camera import MockCamera
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import IMUDataProcessor
from airbrakes.telemetry.logger import Logger
from tests.auxil.utils import make_est_data_packet, make_raw_data_packet

LOG_PATH = Path("tests/logs")
# Get all csv files in the launch_data directory:
LAUNCH_DATA = list(Path("launch_data").glob("*.csv"))
# Remove the genesis_launch_1.csv file since it's almost the same as genesis_launch_2.csv:
LAUNCH_DATA.remove(Path("launch_data/genesis_launch_1.csv"))
# Remove the legacy_launch_2.csv file since it's almost the same as legacy_launch_1.csv:
# LAUNCH_DATA.remove(Path("launch_data/legacy_launch_2.csv"))
# Use the filenames as the ids for the fixtures:
LAUNCH_DATA_IDS = [log.stem for log in LAUNCH_DATA]


@pytest.fixture
def logger():
    """Clear the tests/logs directory before making a new Logger."""
    for log in LOG_PATH.glob("log_*.csv"):
        log.unlink()
    return Logger(LOG_PATH)


@pytest.fixture
def data_processor():
    return IMUDataProcessor()


@pytest.fixture
def imu():
    return IMU(port=IMU_PORT)


@pytest.fixture
def servo():
    return Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))


@pytest.fixture
def apogee_predictor():
    return ApogeePredictor()


@pytest.fixture
def airbrakes(imu, logger, servo, data_processor, apogee_predictor, mock_camera):
    return AirbrakesContext(servo, imu, mock_camera, logger, data_processor, apogee_predictor)


@pytest.fixture
def mock_imu_airbrakes(mock_imu, logger, servo, data_processor, apogee_predictor, mock_camera):
    """Fixture that returns an AirbrakesContext object with a mock IMU. This will run for
    all the launch data files (see the mock_imu fixture)"""
    return AirbrakesContext(servo, mock_imu, mock_camera, logger, data_processor, apogee_predictor)


@pytest.fixture
def random_data_mock_imu():
    # A mock IMU that outputs random data packets
    return RandomDataIMU(port=IMU_PORT)


@pytest.fixture
def idle_mock_imu():
    # A sleeping IMU that doesn't output any data packets
    return IdleIMU(port=IMU_PORT)


@pytest.fixture(params=LAUNCH_DATA, ids=LAUNCH_DATA_IDS)
def mock_imu(request):
    """Fixture that returns a MockIMU object with the specified log file."""
    return MockIMU(log_file_path=request.param, real_time_replay=False, start_after_log_buffer=True)


@pytest.fixture
def camera():
    return Camera()


@pytest.fixture
def mock_camera():
    return MockCamera()


@pytest.fixture
def mocked_args_parser():
    """Fixture that returns a mocked argument parser."""

    class MockArgs:
        mock = True
        real_servo = False
        keep_log_file = False
        fast_replay = False
        debug = False
        path = None
        real_camera = False
        verbose = False
        sim = False

    return MockArgs()


@pytest.fixture
def target_altitude(request):
    """Fixture to return the target altitude based on the mock IMU log file name."""
    # This will be used to set the constants for the test, since they change for different flights:
    # request.node.name is the name of the test function, e.g. test_update[interest_launch]
    launch_name = request.node.name.split("[")[-1].strip("]")
    # We set the target altitude about 50m less than its actual value, since we want to test
    # that the airbrakes deploy before it hits its true apogee.
    if launch_name == "purple_launch":
        return 750.0  # actual apogee was about 794m
    if launch_name == "interest_launch":
        return 1800.0  # actual apogee was about 1854m
    if launch_name == "genesis_launch_2":
        return 413.0  # actual apogee was about 462m
    # if launch_name == "legacy_launch_1":
    #     return 600.0 # actual apogee was about 650m
    return 1000.0  # Default altitude


class RandomDataIMU(IMU):
    """Mocks the data fetch loop, since we don't have the actual IMU to use locally."""

    def _fetch_data_loop(self, _: str) -> None:
        """Output Est and Raw Data packets at the sampling rate we use for the IMU."""
        next_estimated_packet_time = time.time_ns()
        next_raw_packet_time = time.time_ns()

        while self._running.value:
            current_time = time.time_ns()
            # Generate dummy packets, 1 EstimatedDataPacket every 500Hz, and 1 RawDataPacket
            # every 1000Hz
            # sleep for the time it would take to get the next packet
            if current_time >= next_estimated_packet_time:
                estimated_packet = make_est_data_packet(timestamp=current_time * 1e9)
                self._data_queue.put(estimated_packet)
                next_estimated_packet_time += EST_DATA_PACKET_SAMPLING_RATE * 1e9

            if current_time >= next_raw_packet_time:
                raw_packet = make_raw_data_packet(timestamp=current_time * 1e9)
                self._data_queue.put(raw_packet)
                next_raw_packet_time += RAW_DATA_PACKET_SAMPLING_RATE * 1e9

            # Sleep a little to prevent busy-waiting
            time.sleep(0.0005)


class IdleIMU(IMU):
    """Mocks the IMU data fetch loop, but doesn't output any data packets."""

    def _fetch_data_loop(self, _: str) -> None:
        while self.is_running:
            time.sleep(0.1)
