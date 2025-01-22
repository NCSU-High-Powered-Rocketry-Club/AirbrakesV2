"""Module to test the main script."""

import sys
import time
from functools import partial

import gpiozero
import pytest

from airbrakes.constants import LOGS_PATH
from airbrakes.hardware.camera import Camera
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.main import create_components, run_flight, run_mock_flight, run_real_flight
from airbrakes.mock.mock_camera import MockCamera
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import IMUDataProcessor
from airbrakes.telemetry.logger import Logger
from airbrakes.utils import arg_parser


@pytest.fixture(autouse=True)  # autouse=True means run this function before/after every test
def _clear_directory():
    """Clear the tests/logs directory after running each test."""
    yield  # This is where the test runs
    # Test run is over, now clean up
    for log in LOGS_PATH.glob("log_*.csv"):
        log.unlink()


@pytest.fixture
def parsed_args(request, monkeypatch):
    """Fixture to return the parsed arguments."""

    # modify the sys.argv to the arguments passed in the request, so arg_parser can parse them
    # correctly
    monkeypatch.setattr(sys, "argv", request.param)
    return arg_parser()


@pytest.mark.parametrize(
    "parsed_args",
    [
        (["main.py"]),
        (["main.py", "--mock"]),
        (["main.py", "-m", "-r"]),
        (["main.py", "-m", "-r", "-c"]),
        (["main.py", "-m", "-r", "-c", "-l"]),
        (["main.py", "-m", "-r", "-c", "-l", "-f"]),
        (["main.py", "-m", "-r", "-c", "-l", "-f", "-p", "launch_data/something"]),
    ],
    ids=[
        "no-args",
        "mock",
        "mock with real servo",
        "mock with real servo and camera",
        "mock with real servo, camera and log file kept",
        "mock with real servo, camera, log file kept and fast replay",
        "mock with real servo, camera, log file kept, fast replay and specific launch file",
    ],
    indirect=True,
)
def test_create_components(parsed_args, monkeypatch):
    """Tests whether we create the correct components, given the arguments."""

    mock_factory = partial(gpiozero.pins.mock.MockFactory, pin_class=gpiozero.pins.mock.MockPWMPin)

    monkeypatch.setattr("gpiozero.pins.pigpio.PiGPIOFactory", mock_factory)
    created_components = create_components(parsed_args)

    assert len(created_components) == 6
    assert isinstance(created_components[-1], ApogeePredictor)
    assert isinstance(created_components[-2], IMUDataProcessor)

    if parsed_args.mock:
        assert isinstance(created_components[1], MockIMU)
        if parsed_args.fast_replay:
            assert not created_components[1]._data_fetch_process._args[1]
        else:
            assert created_components[1]._data_fetch_process._args[1]

        if parsed_args.path:
            assert created_components[1]._log_file_path == parsed_args.path
        else:
            # First file in the launch_data directory:
            assert "launch_data" in str(created_components[1]._log_file_path)

        # check if the real camera is created:
        if parsed_args.real_camera:
            assert isinstance(created_components[2], Camera)
        else:
            assert isinstance(created_components[2], MockCamera)
    else:
        assert isinstance(created_components[1], IMU)

    if parsed_args.real_servo:
        assert isinstance(created_components[0], Servo)
    else:
        assert isinstance(created_components[0], Servo)
        assert isinstance(created_components[0].servo.pin_factory, gpiozero.pins.mock.MockFactory)

    if parsed_args.keep_log_file:
        assert isinstance(created_components[3], MockLogger)
        assert created_components[3].delete_log_file is False
    else:
        assert isinstance(created_components[3], Logger)


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
    # i.e. test that we didn't pass mock_invocation=True to arg_parser:
    assert not arg_parser_arguments
    # test that we called the arg parser and the run_flight functions
    assert calls == ["parsed arguments", "run_flight"]


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
    # i.e. test that we passed mock_invocation=True to arg_parser:
    assert arg_parser_kwargs == {"mock_invocation": True}
    # test that we called the arg parser and the run_flight functions
    assert calls == ["parsed arguments", "run_flight"]


def test_run_flight(monkeypatch, mocked_args_parser):
    """Tests that the run_flight function initializes the components and runs the flight loop."""
    calls = []
    called_args = []

    def patched_run_flight_loop(*args, **kwargs):
        calls.append("run_flight_loop")

    class PatchedAirbrakesContext:
        def __init__(self, *args, **_):
            calls.append("AirbrakesContext")
            called_args.append(args)

    class PatchedFlightDisplay:
        def __init__(self, *args, **_):
            calls.append("FlightDisplay")
            called_args.append(args)

    monkeypatch.setattr("airbrakes.main.run_flight_loop", patched_run_flight_loop)
    monkeypatch.setattr("airbrakes.main.AirbrakesContext", PatchedAirbrakesContext)
    monkeypatch.setattr("airbrakes.main.FlightDisplay", PatchedFlightDisplay)

    run_flight(mocked_args_parser)

    assert len(calls) == 3
    assert calls == ["AirbrakesContext", "FlightDisplay", "run_flight_loop"]
    assert len(called_args) == 2
    # For airbrakes context, we should have the components as arguments:
    assert len(called_args[0]) == 6  # These are all the components

    # For the flight display, we should have the airbrakes, the mock time start, and the args:
    assert len(called_args[1]) == 3  # These are the airbrakes, the display, and the args
    assert isinstance(called_args[1][0], PatchedAirbrakesContext)
    assert called_args[1][1] == pytest.approx(time.time())
    assert called_args[1][2] == mocked_args_parser
