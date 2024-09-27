"""Module where fixtures are shared between all test files."""

from pathlib import Path

import pytest
from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from constants import FREQUENCY, PORT, SERVO_PIN

LOG_PATH = Path("tests/logs")


@pytest.fixture
def logger():
    """Clear the tests/logs directory before making a new Logger."""
    for log in LOG_PATH.glob("log_*.csv"):
        log.unlink()
    return Logger(LOG_PATH)


@pytest.fixture
def data_processor():
    return IMUDataProcessor([])


@pytest.fixture
def imu():
    return IMU(port=PORT, frequency=FREQUENCY)


@pytest.fixture
def servo():
    return Servo(SERVO_PIN, pin_factory=MockFactory(pin_class=MockPWMPin))


@pytest.fixture
def airbrakes(imu, logger, servo, data_processor):
    return AirbrakesContext(servo, imu, logger, data_processor)
