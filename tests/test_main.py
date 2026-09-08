"""Tests for IMU component construction."""

import sys

import pytest

from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.main import create_components, run_mock_flight, run_real_flight
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.mock.mock_servo import MockServo
from airbrakes.utils import arg_parser


@pytest.fixture
def parsed_args(request, monkeypatch):
    monkeypatch.setattr(sys, "argv", request.param)
    return arg_parser()


@pytest.mark.parametrize(
    "parsed_args",
    [
        ["main.py", "real"],
        ["main.py", "real", "-s"],
        ["main.py", "mock"],
        ["main.py", "mock", "-f"],
        ["main.py", "mock", "-p", "launch_data/purple_launch.csv"],
    ],
    indirect=True,
)
def test_create_components(parsed_args, monkeypatch):
    def mock_servo_init(_self) -> None:
        pass

    monkeypatch.setattr("airbrakes.hardware.servo.Servo.__init__", mock_servo_init)
    components = create_components(parsed_args)

    assert isinstance(components[3], DataProcessor)
    assert isinstance(components[4], ApogeePredictor)
    if parsed_args.mode == "real":
        assert isinstance(components[1], IMU)
        assert isinstance(components[2], Logger)
    else:
        assert isinstance(components[1], MockIMU)
        assert isinstance(components[0], MockServo)
        assert isinstance(components[2], MockLogger)


def test_flight_entry_points_insert_their_mode(monkeypatch):
    calls = []

    def mock_arg_parser() -> object:
        return object()

    def mock_run_flight(_) -> None:
        calls.append(sys.argv[1])

    monkeypatch.setattr("airbrakes.main.arg_parser", mock_arg_parser)
    monkeypatch.setattr("airbrakes.main.run_flight", mock_run_flight)
    run_real_flight()
    run_mock_flight()
    assert calls == ["real", "mock"]
