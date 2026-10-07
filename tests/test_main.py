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
    """Fixture to return parsed command-line arguments."""
    monkeypatch.setattr(sys, "argv", request.param)
    return arg_parser()


@pytest.mark.parametrize(
    "parsed_args",
    [
        (["main.py", "real"]),
        (["main.py", "real", "--mock-servo"]),
        (["main.py", "mock"]),
        (["main.py", "mock", "--real-servo"]),
        (["main.py", "mock", "--real-servo", "--keep-log-file"]),
        (["main.py", "mock", "--real-servo", "--keep-log-file", "--fast-replay"]),
        (
            [
                "main.py",
                "mock",
                "--real-servo",
                "--keep-log-file",
                "--fast-replay",
                "--path",
                "launch_data/purple_launch.csv",
            ]
        ),
    ],
    ids=[
        "real flight with real servo",
        "real flight with mock servo",
        "mock flight with mock servo",
        "mock flight with real servo",
        "mock flight with real servo and kept log",
        "mock flight with real servo, kept log, and fast replay",
        "mock flight with real servo, kept log, fast replay, and specific path",
    ],
    indirect=True,
)
def test_create_components(parsed_args, monkeypatch):
    """Tests that create_components creates the correct components."""
    monkeypatch.setattr(
        "airbrakes.hardware.servo.Servo.__init__",
        lambda *_: None,
    )

    servo, imu, logger, processor, predictor = create_components(parsed_args)

    assert isinstance(processor, DataProcessor)
    assert isinstance(predictor, ApogeePredictor)

    if parsed_args.mode == "real":
        assert isinstance(imu, IMU)
        assert isinstance(logger, Logger)
        assert isinstance(servo, MockServo) is parsed_args.mock_servo

    elif parsed_args.mode == "mock":
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
    """Tests that the CLI rejects unsupported flight modes."""
    monkeypatch.setattr(sys, "argv", ["main.py", "pretend"])

    with pytest.raises(SystemExit):
        arg_parser()


def test_cli_parses_mock_path_as_path_object(monkeypatch):
    """Tests that the CLI converts --path to a Path."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "mock",
            "--fast-replay",
            "--path",
            "launch_data/purple_launch.csv",
        ],
    )

    args = arg_parser()

    assert args.mode == "mock"
    assert args.fast_replay
    assert args.path == Path("launch_data/purple_launch.csv")


def test_run_real_flight(monkeypatch):
    """Tests that run_real_flight parses arguments and selects real mode."""
    calls = []

    def mock_arg_parser():
        calls.append("arg_parser")
        return object()

    def mock_run_flight(args):
        calls.append(("run_flight", args))

    monkeypatch.setattr("airbrakes.main.arg_parser", mock_arg_parser)
    monkeypatch.setattr("airbrakes.main.run_flight", mock_run_flight)

    run_real_flight()

    assert calls[0] == "arg_parser"
    assert calls[1][0] == "run_flight"
    assert sys.argv[1] == "real"


def test_run_mock_flight(monkeypatch):
    """Tests that run_mock_flight parses arguments and selects mock mode."""
    calls = []

    def mock_arg_parser():
        calls.append("arg_parser")
        return object()

    def mock_run_flight(args):
        calls.append(("run_flight", args))

    monkeypatch.setattr("airbrakes.main.arg_parser", mock_arg_parser)
    monkeypatch.setattr("airbrakes.main.run_flight", mock_run_flight)

    run_mock_flight()

    assert calls[0] == "arg_parser"
    assert calls[1][0] == "run_flight"
    assert sys.argv[1] == "mock"


def test_run_flight(monkeypatch, mocked_args_parser):
    """Tests that run_flight wires components into the flight loop."""
    components = (
        object(),
        object(),
        object(),
        object(),
        object(),
    )

    calls = []

    class StubContext:
        def __init__(self, *args):
            calls.append(("context", self, args))

    class StubFlightDisplay:
        def __init__(self, *args):
            calls.append(("display", self, args))

    def mock_run_flight_loop(context, display, is_mock):
        calls.append(("loop", context, display, is_mock))

    monkeypatch.setattr("airbrakes.main.create_components", lambda _: components)
    monkeypatch.setattr("airbrakes.main.Context", StubContext)
    monkeypatch.setattr("airbrakes.main.FlightDisplay", StubFlightDisplay)
    monkeypatch.setattr("airbrakes.main.run_flight_loop", mock_run_flight_loop)

    run_flight(mocked_args_parser)

    assert len(calls) == 3

    # Context was constructed from the components.
    assert calls[0][0] == "context"
    context = calls[0][1]
    assert calls[0][2] == components

    # FlightDisplay was constructed from the Context and arguments.
    assert calls[1][0] == "display"
    display = calls[1][1]
    assert calls[1][2][0] is context
    assert calls[1][2][1] is mocked_args_parser

    # The same Context and FlightDisplay were passed to the flight loop.
    assert calls[2][0] == "loop"
    assert calls[2][1] is context
    assert calls[2][2] is display
    assert calls[2][3] is True
