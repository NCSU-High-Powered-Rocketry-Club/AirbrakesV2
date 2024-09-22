"""Module where fixtures are shared between all test files."""

from pathlib import Path

import pytest
from gpiozero.pins.mock import MockFactory, MockPWMPin

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from constants import FREQUENCY, MAX_EXTENSION, MIN_EXTENSION, PORT, SERVO_PIN, UPSIDE_DOWN

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


@pytest.fixture
def airbrakes(imu, logger, servo):
    return AirbrakesContext(logger, servo, imu)
