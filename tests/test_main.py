"""Module to test the main script."""

import sys

import pytest

from airbrakes.constants import LOGS_PATH
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.firm import FIRM
from airbrakes.hardware.servo import Servo
from airbrakes.main import (
    create_components,
    run_flight,
    run_mock_flight,
    run_real_flight,
)
from airbrakes.mock.mock_firm import MockFIRM
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.mock.mock_servo import MockServo
from airbrakes.utils import arg_parser


class MockedServo:
    """Mocked class for the adafruit.motor servo."""

    def __init__(self, *_, **__):
        self.actuation_range = 180
        self.angle = 0

    def set_pulse_width_range(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _clear_directory():
    """Clear the tests/logs directory after running each test."""
    yield
    for log in LOGS_PATH.glob("log_*.csv"):
        log.unlink()


@pytest.fixture
def parsed_args(request, monkeypatch):
    """Fixture to return the parsed arguments."""
    monkeypatch.setattr(sys, "argv", request.param)
    return arg_parser()


@pytest.mark.parametrize(
    "parsed_args",
    [
        (["main.py", "real"]),
        (["main.py", "real", "-s"]),
        (["main.py", "mock"]),
        (["main.py", "mock", "-s"]),
        (["main.py", "mock", "-s", "-l"]),
        (["main.py", "mock", "-s", "-l", "-f"]),
        (
            [
                "main.py",
                "mock",
                "-s",
                "-l",
                "-f",
                "-p",
                "launch_data/pretended_firm_launches/government_work_1.csv",
            ]
        ),
        (["main.py", "pretend", "-p", "launch_data/raw_firm_data/test.FRM"]),
        (["main.py", "pretend", "-p", "launch_data/raw_firm_data/test.FRM", "-l"]),
        (["main.py", "pretend", "-p", "launch_data/raw_firm_data/test.FRM", "-l", "-s"]),
    ],
    ids=[
        "real flight default (all real)",
        "real with mock servo",
        "mock default (all mock)",
        "mock with real servo",
        "mock with real servo, and log file kept",
        "mock with real servo, log file kept, and fast replay",
        "mock with real servo, log file kept, fast replay, and specific launch file",
        "pretend mode with specific launch file",
        "pretend mode with specific launch file and log file kept",
        "pretend mode with specific launch file and real servo",
    ],
    indirect=True,
)
def test_create_components(parsed_args, monkeypatch):
    """Tests whether we create the correct components, given the arguments."""

    def mock_servo__init__(self, *args, **kwargs):
        pass

    monkeypatch.setattr("airbrakes.hardware.servo.Servo.__init__", mock_servo__init__)

    class MockFIRMClient:
        def __init__(self, *args, **kwargs):
            pass

        def is_running(self):
            return False

        def start(self):
            pass

        def stop(self):
            pass

        def start_mock_log_stream(self, path):
            pass

        def is_mock_log_streaming(self):
            return True

        def get_data_packets(self):
            return []

    monkeypatch.setattr("airbrakes.hardware.firm.FIRMClient", MockFIRMClient)

    created_components = create_components(parsed_args)

    assert len(created_components) == 5
    assert isinstance(created_components[-1], ApogeePredictor)
    assert isinstance(created_components[-2], DataProcessor)

    if parsed_args.mode == "real":
        if parsed_args.mock_servo:
            assert type(created_components[0]) is MockServo
        else:
            assert type(created_components[0]) is Servo

        assert type(created_components[1]) is FIRM
        assert created_components[1].is_pretend is False
        assert type(created_components[2]) is Logger

    elif parsed_args.mode == "mock":
        assert type(created_components[1]) is MockFIRM
        if parsed_args.path:
            assert created_components[1]._log_file_path == parsed_args.path

        if parsed_args.real_servo:
            assert type(created_components[0]) is Servo
        else:
            assert type(created_components[0]) is MockServo

        if parsed_args.fast_replay:
            assert not created_components[1]._data_fetch_thread._args[0]
        else:
            assert created_components[1]._data_fetch_thread._args[0]

        assert type(created_components[2]) is MockLogger
        if parsed_args.keep_log_file:
            assert created_components[2]._delete_log_file is False
        else:
            assert created_components[2]._delete_log_file is True

    elif parsed_args.mode == "pretend":
        assert type(created_components[1]) is FIRM
        assert created_components[1]._log_file_path == parsed_args.path
        assert created_components[1].is_pretend is True
        assert "raw_firm_data" in str(created_components[1]._log_file_path)

        assert type(created_components[2]) is MockLogger
        if parsed_args.keep_log_file:
            assert created_components[2]._delete_log_file is False
        else:
            assert created_components[2]._delete_log_file is True

        if parsed_args.real_servo:
            assert type(created_components[0]) is Servo
        else:
            assert type(created_components[0]) is MockServo


def test_run_real_flight(monkeypatch):
    """Tests the run_real_flight function."""
    arg_parser_arguments = []
    calls = []

    def mock_arg_parser(*args, **kwargs):
        nonlocal arg_parser_arguments, calls
        arg_parser_arguments = args
        calls.append("parsed arguments")

    def patched_run_flight(*args, **kwargs):
        calls.append("run_flight")

    monkeypatch.setattr("airbrakes.main.arg_parser", mock_arg_parser)
    monkeypatch.setattr("airbrakes.main.run_flight", patched_run_flight)

    run_real_flight()

    assert len(calls) == 2
    assert not arg_parser_arguments
    assert calls == ["parsed arguments", "run_flight"]
    assert sys.argv[1] == "real"


def test_run_mock_flight(monkeypatch):
    """Tests the run_mock_flight function."""
    arg_parser_kwargs = []
    calls = []

    def mock_arg_parser(*args, **kwargs):
        nonlocal arg_parser_kwargs, calls
        arg_parser_kwargs = kwargs
        calls.append("parsed arguments")

    def patched_run_flight(*args, **kwargs):
        calls.append("run_flight")

    monkeypatch.setattr("airbrakes.main.arg_parser", mock_arg_parser)
    monkeypatch.setattr("airbrakes.main.run_flight", patched_run_flight)

    run_mock_flight()

    assert len(calls) == 2
    assert not arg_parser_kwargs
    assert calls == ["parsed arguments", "run_flight"]
    assert sys.argv[1] == "mock"


def test_run_flight(monkeypatch, mocked_args_parser):
    """
    Tests that the run_flight function initializes the components and runs
    the flight loop.
    """
    calls = []
    called_args = []

    def patched_run_flight_loop(*args, **kwargs):
        calls.append("run_flight_loop")

    class PatchedContext:
        def __init__(self, *args, **_):
            calls.append("Context")
            called_args.append(args)

    class PatchedFlightDisplay:
        def __init__(self, *args, **_):
            calls.append("FlightDisplay")
            called_args.append(args)

    monkeypatch.setattr("airbrakes.main.run_flight_loop", patched_run_flight_loop)
    monkeypatch.setattr("airbrakes.main.Context", PatchedContext)
    monkeypatch.setattr("airbrakes.main.FlightDisplay", PatchedFlightDisplay)

    run_flight(mocked_args_parser)

    assert len(calls) == 3
    assert calls == ["Context", "FlightDisplay", "run_flight_loop"]
    assert len(called_args) == 2
    assert len(called_args[0]) == 5
    assert len(called_args[1]) == 2
    assert isinstance(called_args[1][0], PatchedContext)
    assert called_args[1][1] == mocked_args_parser
