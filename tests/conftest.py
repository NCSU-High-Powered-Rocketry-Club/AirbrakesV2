"""
Module where fixtures are shared between all test files.
"""

import queue
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from airbrakes.constants import (
    ENCODER_PIN_A,
    ENCODER_PIN_B,
    FIRM_FREQUENCY,
    SERVO_CHANNEL,
)
from airbrakes.context import Context
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.firm import FIRM
from airbrakes.mock.mock_firm import MockFIRM
from airbrakes.mock.mock_servo import MockServo
from tests.auxil.utils import make_firm_data_packet

if TYPE_CHECKING:
    from firm_client import FIRMDataPacket

LOG_PATH = Path("tests/logs")
# Get all csv files in the launch_data directory:
# LAUNCH_DATA = list(Path("launch_data").glob("*.csv"))
# # Remove the genesis_launch_1.csv file since it's almost the same as genesis_launch_2.csv:
# LAUNCH_DATA.remove(Path("launch_data/genesis_launch_1.csv"))
# # Remove the legacy_launch_2.csv file since it failed
# LAUNCH_DATA.remove(Path("launch_data/legacy_launch_2.csv"))
# # Use the filenames as the ids for the fixtures:
# LAUNCH_DATA_IDS = [log.stem for log in LAUNCH_DATA]
LAUNCH_DATA = []
LAUNCH_DATA_IDS = []


@pytest.fixture
def logger():
    """
    Clear the tests/logs directory before making a new Logger.
    """
    for log in LOG_PATH.glob("log_*.csv"):
        log.unlink()
    logger = Logger(LOG_PATH)
    yield logger
    if logger.is_running:
        logger.stop()


@pytest.fixture
def data_processor():
    return DataProcessor()


@pytest.fixture
def firm():
    firm = FIRM()
    yield firm
    if firm.is_running:
        firm.stop()


@pytest.fixture
def servo():
    return MockServo(SERVO_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)


@pytest.fixture
def apogee_predictor():
    return ApogeePredictor()


@pytest.fixture
def context(idle_mock_firm, logger, servo, data_processor, apogee_predictor):
    ab = Context(servo, idle_mock_firm, logger, data_processor, apogee_predictor)
    yield ab
    # Check if something is running:
    if ab.firm.is_running or ab.apogee_predictor.is_running or ab.logger.is_running:
        ab.stop()  # Helps cleanup failing tests that don't stop the airbrakes context


@pytest.fixture
def mock_firm_airbrakes(mock_firm, logger, servo, data_processor, apogee_predictor):
    """
    Fixture that returns an Context object with a mock FIRM.

    This will run for all the launch data files (see the mock_firm fixture)
    """
    ab = Context(servo, mock_firm, logger, data_processor, apogee_predictor)
    yield ab
    # Check if something is running:
    if ab.firm.is_running or ab.apogee_predictor.is_running or ab.logger.is_running:
        ab.stop()


@pytest.fixture
def random_data_mock_firm():
    # A mock FIRM that outputs random data packets
    firm = RandomDataFIRM()
    yield firm
    if firm.is_running:
        firm.stop()


@pytest.fixture
def idle_mock_firm():
    # A sleeping FIRM that doesn't output any data packets
    firm = IdleFIRM()
    yield firm
    if firm.is_running:
        firm.stop()


@pytest.fixture(params=LAUNCH_DATA, ids=LAUNCH_DATA_IDS)
def mock_firm(request):
    """
    Fixture that returns a MockFIRM object with the specified log file.
    """
    # TODO ts isn't finished
    return MockFIRM(
        log_file_path=request.param, real_time_replay=False, start_after_log_buffer=True
    )


@pytest.fixture
def mocked_args_parser():
    """
    Fixture that returns a mocked argument parser.
    """

    class MockArgs:
        mode = "mock"
        real_servo = False
        keep_log_file = False
        fast_replay = False
        debug = False
        path = None
        verbose = False
        sim = False
        real_firm = False
        pretend_firm = False
        mock_firm = None

    return MockArgs()


@pytest.fixture
def target_altitude(request):
    """
    Fixture to return the target altitude based on the mock FIRM log file name.
    """
    # This will be used to set the constants for the test, since they change for different flights:
    # request.node.name is the name of the test function, e.g. test_update[shake_n_bake]
    launch_name = request.node.name.split("[")[-1].strip("]")
    # We set the target altitude about 50m less than its actual value, since we want to test
    # that the airbrakes deploy before it hits its true apogee.
    if launch_name == "purple_launch":
        return 750.0  # actual apogee was about 794m
    if launch_name == "shake_n_bake":
        return 1800.0  # actual apogee was about 1854m
    if launch_name == "genesis_launch_2":
        return 413.0  # actual apogee was about 462m
    if launch_name == "legacy_launch_1":
        return 580.0  # actual apogee was about 631.14m
    # Airbrakes actually deployed on this flight, and we had set an apogee higher than the actual
    # apogee achieved because of the airbrakes.
    if launch_name == "pelicanator_launch_1":
        return 1218.9  # actual apogee was about 1208.9m
    if launch_name == "pelicanator_launch_2":
        return 1127.76  # actual apogee was about 1090.16m
    # Airbrakes actually deployed on this flight-
    if launch_name == "pelicanator_launch_3":
        return 1110.6  # actual apogee was about 1160.6m
    if launch_name == "pelicanator_launch_4":
        return 1200.0  # actual apogee was about 1293.72m
    if launch_name == "government_work_1":
        return 360.0  # actual apogee was about 400m
    if launch_name == "government_work_2":
        return 674.13  # actual apogee was about 724.13m
    return 1000.0  # Default altitude


class RandomDataFIRM(FIRM):
    """
    Mocks the FIRM device by generating random FIRMDataPackets internally
    on a separate thread at FIRM_FREQUENCY.
    """

    __slots__ = ("_queue", "_stop_event", "_thread")

    def __init__(self):
        # We override __init__ completely to bypass FIRMClient connection logic.
        self._queue = queue.SimpleQueue()
        self._stop_event = threading.Event()
        self._thread = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Starts the background thread that generates fake packets."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._generation_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the background generation thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join()
        self._thread = None

    def get_data_packets(self) -> list[FIRMDataPacket]:
        """Returns all packets currently in the internal queue."""
        packets = []
        while not self._queue.empty():
            packets.append(self._queue.get())
        return packets

    def _generation_loop(self) -> None:
        """Generates packets at FIRM_FREQUENCY."""
        interval_ns = int((1.0 / FIRM_FREQUENCY) * 1e9)
        next_tick_ns = time.time_ns()

        while not self._stop_event.is_set():
            now_ns = time.time_ns()

            if now_ns >= next_tick_ns:
                # Generate packet with current timestamp
                packet = make_firm_data_packet(timestamp_seconds=now_ns / 1e9)
                self._queue.put(packet)

                next_tick_ns += interval_ns

            # Sleep until the next tick to prevent CPU spinning
            remaining_ns = next_tick_ns - time.time_ns()
            if remaining_ns > 0:
                time.sleep(remaining_ns / 1e9)


class IdleFIRM(FIRM):
    """
    Mocks a connected FIRM device that simply outputs no data.
    """

    __slots__ = ("_queue", "_running")

    def __init__(self):
        self._queue = queue.SimpleQueue()
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def get_data_packets(self) -> list[FIRMDataPacket]:
        packets = []
        while not self._queue.empty():
            packets.append(self._queue.get())
        return packets
