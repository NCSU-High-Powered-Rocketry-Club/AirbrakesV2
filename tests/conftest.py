"""Module where fixtures are shared between all test files."""

from pathlib import Path

import pytest
from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.constants import FREQUENCY, MAX_EXTENSION, MIN_EXTENSION, PORT, SERVO_PIN, UPSIDE_DOWN
from airbrakes.imu.imu import IMU
from airbrakes.logger import Logger
from airbrakes.servo import Servo

LOG_PATH = Path("tests/logs")


@pytest.fixture
def logger():
    return Logger(LOG_PATH)


@pytest.fixture
def imu():
    return IMU(port=PORT, frequency=FREQUENCY, upside_down=UPSIDE_DOWN)


@pytest.fixture
def servo():
    return Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION, pin_factory=MockFactory(pin_class=MockPWMPin))