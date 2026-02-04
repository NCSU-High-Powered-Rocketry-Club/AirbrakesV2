"""
Module to test the main script.
"""

import sys
from functools import partial
from pathlib import Path

import gpiozero
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
    """
    Mocked class for the adafruit.motor servo.
    """

    def __init__(self, *_, **__):
        self.actuation_range = 180
        self.angle = 0

    def set_pulse_width_range(self, *args, **kwargs):
        pass


@pytest.fixture(autouse=True)
def _clear_directory():
    """
    Clear the tests/logs directory after running each test.
    """
    yield
    for log in LOGS_PATH.glob("log_*.csv"):
        log.unlink()


@pytest.fixture
def parsed_args(request, monkeypatch):
    """
    Fixture to return the parsed arguments.
    """
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
        # Mock mode, but using FIRM class in pretend mode
        (["main.py", "mock", "-p", "launch_data/shake_n_bake.csv"]),
        # Mock mode, using MockFIRM class with explicit file
        (["main.py", "mock", "-m", "launch_data/shake_n_bake.csv"]),
    ],
    ids=[
        "real flight default (all real)",
        "real with mock servo",
        "mock default (all mock)",
        "mock with real servo",
        "mock with real servo, and log file kept",
        "mock with real servo, log file kept, and fast replay",
        "mock with Pretend FIRM (real class, pretend mode)",
        "mock with Mock FIRM (mock class, explicit file)",
    ],
    indirect=True,
)
def test_create_components(parsed_args, monkeypatch):
    """
    Tests whether we create the correct components, given the arguments.
    """
    # 1. Mock GPIO for Servo
    mock_factory = partial(gpiozero.pins.mock.MockFactory, pin_class=gpiozero.pins.mock.MockPWMPin)

    def mock_servo__init__(self, *args, **kwargs):
        """Mock the __init__ of the airbrakes Servo class."""
        pass

    monkeypatch.setattr("gpiozero.pins.native.NativeFactory", mock_factory)
    monkeypatch.setattr("airbrakes.hardware.servo.Servo.__init__", mock_servo__init__)

    # 2. Mock FIRMClient so FIRM() doesn't try to open real serial ports
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

    # 3. Create the components
    created_components = create_components(parsed_args)

    assert len(created_components) == 5
    assert isinstance(created_components[-1], ApogeePredictor)
    assert isinstance(created_components[-2], DataProcessor)

    # --- REAL MODE CHECKS ---
    if parsed_args.mode == "real":
        # Servo Checks
        if parsed_args.mock_servo:
            assert type(created_components[0]) is MockServo
        else:
            assert type(created_components[0]) is Servo

        # FIRM Checks
        # In real mode, it must be FIRM, and pretend must be False
        assert type(created_components[1]) is FIRM
        assert created_components[1].is_pretend is False

        # Logger Checks
        assert type(created_components[2]) is Logger

    # --- MOCK MODE CHECKS ---
    elif parsed_args.mode == "mock":
        # Servo Checks
        if parsed_args.real_servo:
            assert type(created_components[0]) is Servo
        else:
            assert type(created_components[0]) is MockServo

        # FIRM Checks (The Logic Change is Here)
        if parsed_args.pretend_firm:
            # If -p is passed, we use the REAL FIRM class, but with is_pretend=True
            assert type(created_components[1]) is FIRM
            assert created_components[1].is_pretend is True
            # Check if the path was passed correctly
            assert str(created_components[1]._log_file_path) == parsed_args.pretend_firm
        else:
            # Otherwise we use the MockFIRM class (pure python simulation)
            assert type(created_components[1]) is MockFIRM

            if parsed_args.mock_firm:
                assert created_components[1]._log_file_path == parsed_args.mock_firm
            else:
                assert "launch_data" in str(created_components[1]._log_file_path)

            # Fast replay only applies to MockFIRM
            if parsed_args.fast_replay:
                assert not created_components[1]._data_fetch_thread._args[0]
            else:
                assert created_components[1]._data_fetch_thread._args[0]

        # Logger Checks
        assert type(created_components[2]) is MockLogger
        if parsed_args.keep_log_file:
            assert created_components[2]._delete_log_file is False
        else:
            assert created_components[2]._delete_log_file is True


def test_run_real_flight(monkeypatch):
    """
    Tests the run_real_flight function.
    """
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
    """
    Tests the run_mock_flight function.
    """
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
    Tests that the run_flight function initializes the components and runs the flight loop.
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
    # Check components
    assert len(called_args[0]) == 5

    # Check FlightDisplay args
    assert len(called_args[1]) == 2
    assert isinstance(called_args[1][0], PatchedContext)
    assert called_args[1][1] == mocked_args_parser
