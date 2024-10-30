"""Module where fixtures are shared between all test files."""

import time
from pathlib import Path

import pytest
from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.mock.mock_imu import MockIMU
from constants import FREQUENCY, PORT, SERVO_PIN

LOG_PATH = Path("tests/logs")
# Get all csv files in the launch_data directory:
LAUNCH_DATA = list(Path("launch_data").glob("*.csv"))
# Use the filenames as the ids for the fixtures:
LAUNCH_DATA_IDS = [log.stem for log in LAUNCH_DATA]
RAW_DATA_PACKET_SAMPLING_RATE = 1 / 1000  # 1kHz
EST_DATA_PACKET_SAMPLING_RATE = 1 / 500  # 500Hz


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
    return IMU(port=PORT, frequency=FREQUENCY)


@pytest.fixture
def servo():
    return Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))


@pytest.fixture
def airbrakes(imu, logger, servo, data_processor):
    return AirbrakesContext(servo, imu, logger, data_processor)


@pytest.fixture
def random_data_mock_imu():
    return RandomDataIMU(port=PORT, frequency=FREQUENCY)


@pytest.fixture(params=LAUNCH_DATA, ids=LAUNCH_DATA_IDS)
def mock_imu(request):
    """Fixture that returns a MockIMU object with the specified log file."""
    return MockIMU(log_file_path=request.param, real_time_simulation=False)


class RandomDataIMU(IMU):
    """Mocks the data fetch loop, since we don't have the actual IMU to use locally."""

    def _fetch_data_loop(self, _: str, __: int) -> None:
        """Output Est and Raw Data packets at the sampling rate we use for the IMU."""
        next_estimated_packet_time = time.time()
        next_raw_packet_time = time.time()

        while self._running.value:
            current_time = time.time()
            # Generate dummy packets, 1 EstimatedDataPacket every 500Hz, and 1 RawDataPacket
            # every 1000Hz
            # sleep for the time it would take to get the next packet
            if current_time >= next_estimated_packet_time:
                estimated_packet = EstimatedDataPacket(timestamp=current_time * 1e9)
                self._data_queue.put(estimated_packet)
                next_estimated_packet_time += EST_DATA_PACKET_SAMPLING_RATE

            if current_time >= next_raw_packet_time:
                raw_packet = RawDataPacket(timestamp=current_time * 1e9)
                self._data_queue.put(raw_packet)
                next_raw_packet_time += RAW_DATA_PACKET_SAMPLING_RATE

            # Sleep a little to prevent busy-waiting
            time.sleep(0.001)
