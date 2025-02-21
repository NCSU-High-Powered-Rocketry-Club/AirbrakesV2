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
from airbrakes.main import (
    create_components,
    run_flight,
    run_mock_flight,
    run_real_flight,
    run_sim_flight,
)
from airbrakes.mock.mock_camera import MockCamera
from airbrakes.mock.mock_imu import MockIMU
from airbrakes.mock.mock_logger import MockLogger
from airbrakes.mock.mock_servo import MockServo
from airbrakes.simulation.sim_imu import SimIMU
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import IMUDataProcessor
from airbrakes.telemetry.logger import Logger
from airbrakes.utils import arg_parser


class MockedServoKit:
    """Mocked class for the real servo."""

    def __init__(self, channels: int, *_, **__):
        self.servo = [MockedServo()] * channels


class MockedServo:
    """Mocked class for the adafruit.motor servo."""

    def __init__(self, *_, **__):
        self.actuation_range = 180
        self.angle = 0

    def set_pulse_width_range(self, *args, **kwargs):
        pass


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


@pytest.mark.skipif(sys.platform == "arm64", reason="This test is not supported on arm64.")
@pytest.mark.parametrize(
    "parsed_args",
    [
        (["main.py", "real"]),
        (["main.py", "mock"]),
        (["main.py", "mock", "-r"]),
        (["main.py", "mock", "-r", "-c"]),
        (["main.py", "mock", "-r", "-c", "-l"]),
        (["main.py", "mock", "-r", "-c", "-l", "-f"]),
        (["main.py", "mock", "-r", "-c", "-l", "-f", "-p", "launch_data/something"]),
        (
            [
                "main.py",
                "sim",
                "sub-scale",
                "-r",
            ]
        ),
    ],
    ids=[
        "real flight",
        "mock",
        "mock with real servo",
        "mock with real servo and camera",
        "mock with real servo, camera and log file kept",
        "mock with real servo, camera, log file kept and fast replay",
        "mock with real servo, camera, log file kept, fast replay and specific launch file",
        "sim with real servo",
    ],
    indirect=True,
)
def test_create_components(parsed_args, monkeypatch):
    """Tests whether we create the correct components, given the arguments."""

    mock_factory = partial(gpiozero.pins.mock.MockFactory, pin_class=gpiozero.pins.mock.MockPWMPin)

    monkeypatch.setattr("airbrakes.hardware.servo.ServoKit", MockedServoKit)
    monkeypatch.setattr("gpiozero.pins.native.NativeFactory", mock_factory)
    created_components = create_components(parsed_args)

    assert len(created_components) == 6
    assert isinstance(created_components[-1], ApogeePredictor)
    assert isinstance(created_components[-2], IMUDataProcessor)

    if parsed_args.mode in ("mock", "sim"):
        if parsed_args.mode == "mock":
            assert type(created_components[1]) is MockIMU

            if parsed_args.path:
                assert created_components[1]._log_file_path == parsed_args.path
            else:
                # First file in the launch_data directory:
                assert "launch_data" in str(created_components[1]._log_file_path)

        else:  # sim
            assert type(created_components[1]) is SimIMU

        if parsed_args.fast_replay:
            assert not created_components[1]._data_fetch_process._args[1]
        else:
            assert created_components[1]._data_fetch_process._args[1]

        # check if the real camera is created:
        if parsed_args.real_camera:
            assert type(created_components[2]) is Camera
        else:
            assert type(created_components[2]) is MockCamera

        # This particular test case is bad, I'm not testing whether our pin factory is PiGPIO or not
        # since I don't want to run the constructor of that class, which errors out.
        # TODO: Use a magic mock?
        if parsed_args.real_servo:
            assert type(created_components[0]) is Servo
        else:
            assert type(created_components[0]) is MockServo
            assert isinstance(
                created_components[0].encoder.pin_factory, gpiozero.pins.mock.MockFactory
            )

        # A mock logger object is always created:
        assert type(created_components[3]) is MockLogger
        if parsed_args.keep_log_file:
            assert created_components[3]._delete_log_file is False
        else:
            assert created_components[3]._delete_log_file is True

    # Real hardware components:
    else:
        assert type(created_components[1]) is IMU
        assert type(created_components[0]) is Servo
        assert type(created_components[2]) is Camera
        assert type(created_components[3]) is Logger


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
    # i.e. test that we didn't pass any arguments to the arg_parser:
    assert not arg_parser_arguments
    # test that we called the arg parser and the run_flight functions
    assert calls == ["parsed arguments", "run_flight"]
    # Test that we modified sys.argv to include "real":
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
    # i.e. test that we passed no arguments to the arg_parser:
    assert not arg_parser_kwargs
    # test that we called the arg parser and the run_flight functions
    assert calls == ["parsed arguments", "run_flight"]
    # Test that we modified sys.argv to include "mock":
    assert sys.argv[1] == "mock"


def test_run_sim_flight(monkeypatch):
    """Tests the run_sim_flight function."""
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

    run_sim_flight()

    assert len(calls) == 2
    # i.e. test that we passed no arguments to the arg_parser:
    assert not arg_parser_kwargs
    # test that we called the arg parser and the run_flight functions
    assert calls == ["parsed arguments", "run_flight"]
    # Test that we modified sys.argv to include "sim":
    assert sys.argv[1] == "sim"


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
