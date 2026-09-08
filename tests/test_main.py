"""Tests for IMU CLI parsing and application component construction."""

import sys
from pathlib import Path

import pytest

from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU
from airbrakes.main import create_components, run_flight, run_mock_flight, run_real_flight
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
        ["main.py", "real", "--mock-servo"],
        ["main.py", "mock"],
        ["main.py", "mock", "--real-servo", "--keep-log-file", "--fast-replay"],
        ["main.py", "mock", "--path", "launch_data/purple_launch.csv"],
    ],
    indirect=True,
)
def test_create_components_for_supported_imu_modes(parsed_args, monkeypatch):
    monkeypatch.setattr("airbrakes.hardware.servo.Servo.__init__", lambda _: None)

    servo, imu, logger, processor, predictor = create_components(parsed_args)

    assert isinstance(processor, DataProcessor)
    assert isinstance(predictor, ApogeePredictor)
    if parsed_args.mode == "real":
        assert isinstance(imu, IMU)
        assert isinstance(logger, Logger)
        assert isinstance(servo, MockServo) is parsed_args.mock_servo
    else:
        assert isinstance(imu, MockIMU)
        assert isinstance(logger, MockLogger)
        assert isinstance(servo, MockServo) is not parsed_args.real_servo
        if parsed_args.path is not None:
            assert imu.log_file_path == parsed_args.path
        else:
            assert imu.log_file_path.parent.name == "launch_data"
        assert imu._data_fetch_thread._args[0] is (not parsed_args.fast_replay)
        assert logger._delete_log_file is (not parsed_args.keep_log_file)


def test_cli_only_accepts_real_and_mock_modes(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main.py", "pretend"])

    with pytest.raises(SystemExit):
        arg_parser()


def test_cli_parses_mock_path_as_path_object(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "mock", "--fast-replay", "--path", "launch_data/purple_launch.csv"],
    )

    args = arg_parser()

    assert args.mode == "mock"
    assert args.fast_replay
    assert args.path == Path("launch_data/purple_launch.csv")


def test_flight_entry_points_insert_their_mode(monkeypatch):
    calls = []

    def parse_arguments():
        return object()

    monkeypatch.setattr("airbrakes.main.run_flight", lambda _: calls.append(sys.argv[1]))
    monkeypatch.setattr("airbrakes.main.arg_parser", parse_arguments)

    run_real_flight()
    run_mock_flight()

    assert calls == ["real", "mock"]


def test_run_flight_wires_components_context_display_and_loop(monkeypatch, mocked_args_parser):
    calls = []
    components = (object(), object(), object(), object(), object())

    class StubContext:
        def __init__(self, *args):
            calls.append(("context", args))

    class StubDisplay:
        def __init__(self, *args):
            calls.append(("display", args))

    monkeypatch.setattr("airbrakes.main.create_components", lambda _: components)
    monkeypatch.setattr("airbrakes.main.Context", StubContext)
    monkeypatch.setattr("airbrakes.main.FlightDisplay", StubDisplay)
    monkeypatch.setattr(
        "airbrakes.main.run_flight_loop",
        lambda context, display, is_mock: calls.append(("loop", context, display, is_mock)),
    )
    monkeypatch.setattr("airbrakes.main.sysconfig.get_config_var", lambda _: True)
    monkeypatch.setattr("airbrakes.main.sys._is_gil_enabled", lambda: False)

    run_flight(mocked_args_parser)

    assert calls[0] == ("context", components)
    assert calls[1][0] == "display"
    assert calls[1][1][1] is mocked_args_parser
    assert calls[2][0] == "loop"
    assert calls[2][-1] is True
