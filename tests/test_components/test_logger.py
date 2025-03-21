import csv
import multiprocessing
import multiprocessing.sharedctypes
import threading
import time
from collections import deque
from functools import partial

import faster_fifo
import pytest
from msgspec.structs import asdict

from airbrakes.constants import (
    IDLE_LOG_CAPACITY,
    LOG_BUFFER_SIZE,
    NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
    STOP_SIGNAL,
)
from airbrakes.telemetry.logger import Logger
from airbrakes.telemetry.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket
from airbrakes.telemetry.packets.imu_data_packet import (
    IMUDataPacket,
)
from airbrakes.telemetry.packets.logger_data_packet import LoggerDataPacket
from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.telemetry.packets.servo_data_packet import ServoDataPacket
from tests.auxil.utils import (
    make_apogee_predictor_data_packet,
    make_context_data_packet,
    make_est_data_packet,
    make_processor_data_packet,
    make_raw_data_packet,
    make_servo_data_packet,
)
from tests.conftest import LOG_PATH


def patched_stop(self):
    """Monkeypatched stop method which does not log the buffer."""
    # Make sure the rest of the code is the same as the original method!
    self._log_queue.put(STOP_SIGNAL)
    self._log_process.join()


def remove_state_letter(debug_packet_dict: dict[str, str]) -> dict[str, str]:
    """Helper method which removes the state letter from the dictionary and returns the modified
    dictionary."""
    debug_packet_dict.pop("state_letter")
    return debug_packet_dict


def only_logged_pdp_fields(pdp_dict: dict[str, str]) -> dict[str, str]:
    """Returns a dictionary with only the fields that are logged in the ProcessorDataPacket."""
    pdp_dict.pop("time_since_last_data_packet")
    return pdp_dict


def convert_dict_vals_to_str(d: dict[str, float], truncation: bool = True) -> dict[str, str]:
    """Converts all values in the dictionary to strings. Applies truncation for floats by default.
    Drops None values."""
    new_d = {}
    for k, v in d.items():
        if isinstance(v, int):
            new_d[k] = str(v)
        elif v is None:  # Skip None values
            continue
        elif truncation:
            try:
                # Try converting to float and format with the given precision
                new_d[k] = f"{float(v):.8f}"
            except (ValueError, TypeError):
                # If conversion fails, just convert the value to a plain string
                new_d[k] = str(v)
        else:
            new_d[k] = str(v)
    return new_d


@pytest.fixture
def threaded_logger(monkeypatch):
    """Modifies the Logger to run in a separate thread instead of a process."""
    logger = Logger(LOG_PATH)
    # Cannot use signals from child threads, so we need to monkeypatch it:
    monkeypatch.setattr("signal.signal", lambda _, __: None)
    target = threading.Thread(target=logger._logging_loop)
    logger._log_process = target
    yield logger
    logger.stop()


class TestLogger:
    """Tests the Logger() class in logger.py"""

    sample_ldp = LoggerDataPacket(
        state_letter="S",
        set_extension="0.0",
        timestamp=4,
        invalid_fields=[],
        encoder_position=None,
        imu_packets_per_cycle=None,
        retrieved_imu_packets=None,
        queued_imu_packets=None,
        apogee_predictor_queue_size=None,
        update_timestamp_ns=None,
    )

    @pytest.fixture(autouse=True)  # autouse=True means run this function before/after every test
    def _clear_directory(self):
        """Clear the tests/logs directory after running each test."""
        yield  # This is where the test runs
        # Test run is over, now clean up
        for log in LOG_PATH.glob("log_*.csv"):
            log.unlink()

    def test_slots(self, logger):
        inst = logger
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, logger):
        # Test if "logs" directory was created
        assert logger.log_path.parent.exists()
        assert logger.log_path.parent.name == "logs"

        # Test if all attributes are created correctly
        assert isinstance(logger._log_queue, faster_fifo.Queue)
        assert isinstance(logger._log_process, multiprocessing.Process)

        # Test that the process is not running
        assert not logger.is_running
        assert not logger._log_process.is_alive()

    def test_init_sets_log_path_correctly(self):
        # assert no files exist:
        assert not list(LOG_PATH.glob("log_*.csv"))
        logger = Logger(LOG_PATH)
        expected_log_path = LOG_PATH / "log_1.csv"
        assert expected_log_path.exists()
        assert logger.log_path == expected_log_path
        logger_2 = Logger(LOG_PATH)
        expected_log_path_2 = LOG_PATH / "log_2.csv"
        assert expected_log_path_2.exists()
        assert logger_2.log_path == expected_log_path_2

        # Test only 2 csv files exist:
        assert set(LOG_PATH.glob("log_*.csv")) == {expected_log_path, expected_log_path_2}

    def test_init_log_file_has_correct_headers(self, logger):
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            keys = reader.fieldnames
            assert list(keys) == list(LoggerDataPacket.__struct_fields__)

    def test_log_buffer_is_full_property(self, logger):
        """Tests whether the property is_log_buffer_full works correctly."""
        assert not logger.is_log_buffer_full
        logger._log_buffer.extend([1] * (LOG_BUFFER_SIZE - 1))
        assert not logger.is_log_buffer_full
        logger._log_buffer.clear()
        assert len(logger._log_buffer) == 0
        logger._log_buffer.extend([1] * LOG_BUFFER_SIZE)
        assert logger.is_log_buffer_full

    def test_logger_stops_on_stop_signal(self, logger):
        """Tests whether the logger stops when it receives a stop signal."""
        logger.start()
        logger._log_queue.put(STOP_SIGNAL)
        time.sleep(0.01)
        assert not logger.is_running
        assert not logger._log_process.is_alive()
        logger.stop()

    def test_logging_loop_start_stop(self, logger):
        logger.start()
        assert logger.is_running

        logger.stop()
        assert not logger.is_running
        assert logger._log_process.exitcode == 0

    def test_logger_stop_logs_the_buffer(self, logger):
        logger.start()
        logger._log_buffer.appendleft(self.sample_ldp)
        logger.stop()
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, row in enumerate(reader):
                count = idx + 1
                assert len(row) > 5  # Should have other fields with empty values
                # Only fetch non-empty values:
                row_dict = {k: v for k, v in row.items() if v}
                assert row_dict == convert_dict_vals_to_str(asdict(self.sample_ldp), False)
            assert count == 1
        assert len(logger._log_buffer) == 0

    def test_logger_ctrl_c_handling(self, monkeypatch):
        """Tests whether the Logger handles Ctrl+C events from main loop correctly."""
        values = faster_fifo.Queue()
        org_method = Logger._logging_loop

        def _logging_loop_patched(self):
            """Monkeypatched method for testing."""
            org_method(self)
            values.put("clean exit")

        monkeypatch.setattr(Logger, "_logging_loop", _logging_loop_patched)

        logger = Logger(LOG_PATH)
        logger.start()
        assert logger.is_running
        assert values.qsize() == 0
        try:
            raise KeyboardInterrupt  # send a KeyboardInterrupt to test __exit__
        except KeyboardInterrupt:
            logger.stop()

        assert not logger.is_running
        assert not logger._log_process.is_alive()
        assert values.qsize() == 1
        assert values.get() == "clean exit"

    def test_logging_loop_add_to_queue(self, logger):
        logger._log_queue.put(self.sample_ldp)
        assert logger._log_queue.qsize() == 1
        logger.start()
        time.sleep(0.01)  # Give the process time to log to file
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                row: dict[str]
            # Only fetch non-empty values:
            row_dict = {k: v for k, v in row.items() if v}

            assert row_dict == convert_dict_vals_to_str(asdict(self.sample_ldp), truncation=False)

    def test_queue_hits_timeout_and_continues(self, logger, monkeypatch):
        """Tests whether the logger continues to log after a timeout."""
        monkeypatch.setattr("airbrakes.telemetry.logger.MAX_GET_TIMEOUT_SECONDS", 0.01)
        logger.start()
        time.sleep(0.05)
        logger._log_queue.put(self.sample_ldp)
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            row = {}
            for row in reader:
                row: dict[str]
            # Only fetch non-empty values:
            row_dict = {k: v for k, v in row.items() if v}

            assert row_dict == convert_dict_vals_to_str(asdict(self.sample_ldp), truncation=False)

    # This decorator is used to run the same test with different data
    # read more about it here: https://docs.pytest.org/en/stable/parametrize.html
    @pytest.mark.parametrize(
        (
            "context_packet",
            "servo_packet",
            "imu_data_packets",
            "processor_data_packets",
            "apogee_predictor_data_packets",
            "file_lines",
            "expected_output",
        ),
        [
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_raw_data_packet()]),
                [],
                [],
                1,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state_letter="S"))
                        ),
                        **asdict(make_servo_data_packet(set_extension="0.0")),
                        **convert_dict_vals_to_str(asdict(make_raw_data_packet())),
                    }
                ],
            ),
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                1,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state_letter="S"))
                        ),
                        **asdict(make_servo_data_packet(set_extension="0.0")),
                        **convert_dict_vals_to_str(asdict(make_est_data_packet())),
                        **only_logged_pdp_fields(
                            convert_dict_vals_to_str(asdict(make_processor_data_packet()))
                        ),
                    }
                ],
            ),
            (
                make_context_data_packet(state_letter="M"),
                make_servo_data_packet(set_extension="0.5"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                2,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state_letter="M"))
                        ),
                        **asdict(make_servo_data_packet(set_extension="0.5")),
                        **convert_dict_vals_to_str(asdict(make_raw_data_packet())),
                    },
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state_letter="M"))
                        ),
                        **asdict(make_servo_data_packet(set_extension="0.5")),
                        **convert_dict_vals_to_str(asdict(make_est_data_packet())),
                        **only_logged_pdp_fields(
                            convert_dict_vals_to_str(asdict(make_processor_data_packet()))
                        ),
                    },
                ],
            ),
            (
                make_context_data_packet(state_letter="C"),
                make_servo_data_packet(set_extension="0.4"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [make_apogee_predictor_data_packet()],
                2,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state_letter="C"))
                        ),
                        **asdict(make_servo_data_packet(set_extension="0.4")),
                        **convert_dict_vals_to_str(asdict(make_raw_data_packet())),
                        **convert_dict_vals_to_str(asdict(make_apogee_predictor_data_packet())),
                    },
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state_letter="C"))
                        ),
                        **asdict(make_servo_data_packet(set_extension="0.4")),
                        **convert_dict_vals_to_str(asdict(make_est_data_packet())),
                        **only_logged_pdp_fields(
                            convert_dict_vals_to_str(asdict(make_processor_data_packet()))
                        ),
                    },
                ],
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
            "BothDataPackets in MotorBurn",
            "BothDataPackets in Coast",
        ],
    )
    def test_log_method(
        self,
        logger,
        context_packet,
        servo_packet,
        imu_data_packets,
        processor_data_packets,
        apogee_predictor_data_packets,
        file_lines,
        expected_output: list[dict],
    ):
        """Tests whether the log method logs the data correctly to the CSV file."""
        logger.start()

        logger.log(
            context_packet,
            servo_packet,
            imu_data_packets.copy(),
            processor_data_packets.copy(),
            apogee_predictor_data_packets.copy(),
        )
        time.sleep(0.01)  # Give the process time to log to file
        logger.stop()

        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)

            # The row with the data packet:
            row: dict[str, str]
            idx = -1
            for idx, row in enumerate(reader):
                # Only fetch non-empty values:
                row_dict_non_empty = {k: v for k, v in row.items() if v}
                # Random check to make sure we aren't missing any fields
                assert len(row_dict_non_empty) > 19

                assert row_dict_non_empty == expected_output[idx]

            assert idx + 1 == file_lines

    @pytest.mark.parametrize(
        (
            "context_packet",
            "servo_packet",
            "imu_data_packets",
            "processor_data_packets",
            "apogee_predictor_data_packets",
        ),
        [
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_raw_data_packet()]),
                [],
                [],
            ),
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [make_apogee_predictor_data_packet()],
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_log_capacity_exceeded_standby(
        self,
        context_packet: ContextDataPacket,
        servo_packet: ServoDataPacket,
        imu_data_packets: deque[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packets: list[ApogeePredictorDataPacket],
        monkeypatch,
        logger,
    ):
        """Tests whether the log buffer works correctly for the Standby and Landed state."""

        monkeypatch.setattr(logger.__class__, "stop", patched_stop)
        # Test if the buffer works correctly
        logger.start()
        # Log more than IDLE_LOG_CAPACITY packets to test if it stops logging after LOG_BUFFER_SIZE.
        logger.log(
            context_packet,
            servo_packet,
            imu_data_packets * (IDLE_LOG_CAPACITY + 10),
            processor_data_packets * (IDLE_LOG_CAPACITY + 10),
            apogee_predictor_data_packets,
        )

        time.sleep(0.01)  # Give the process time to log to file
        # Since we did +10 above, we should have 10 left in the buffer
        assert len(logger._log_buffer) == 10
        logger.stop()  # We must stop because otherwise the values are not flushed to the file

        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, _ in enumerate(reader):
                count = idx

            # First row index is zero, hence the +1
            assert count + 1 == IDLE_LOG_CAPACITY
            assert logger._log_counter == IDLE_LOG_CAPACITY

    @pytest.mark.parametrize(
        (
            "context_packet",
            "servo_packet",
            "imu_data_packets",
            "processor_data_packets",
            "apogee_predictor_data_packets",
        ),
        [
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_raw_data_packet()]),
                [],
                [],
            ),
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [make_apogee_predictor_data_packet()],
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_log_buffer_keeps_increasing(
        self,
        context_packet: ContextDataPacket,
        servo_packet: ServoDataPacket,
        imu_data_packets: deque[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packets: list[ApogeePredictorDataPacket],
        logger,
    ):
        """Tests that the buffer keeps building up on subsequent calls to log()."""

        # Test if the buffer works correctly
        logger.start()
        # Log more than IDLE_LOG_CAPACITY packets to test if packets go to the buffer.
        logger.log(
            context_packet,
            servo_packet,
            imu_data_packets * (IDLE_LOG_CAPACITY + 10),
            processor_data_packets * (IDLE_LOG_CAPACITY + 10),
            apogee_predictor_data_packets,
        )

        # Log more than LOG_BUFFER_SIZE packets to test if the buffer keeps building.
        logger.log(
            context_packet,
            servo_packet,
            imu_data_packets * (LOG_BUFFER_SIZE + 10),
            processor_data_packets * (LOG_BUFFER_SIZE + 10),
            apogee_predictor_data_packets,
        )

        time.sleep(0.01)  # Give the process time to log to file

        assert len(logger._log_buffer) == LOG_BUFFER_SIZE
        logger.stop()  # We must stop because otherwise the values are not flushed to the file
        assert len(logger._log_buffer) == 0

        with logger.log_path.open() as file:
            lines = file.readlines()
            # First row is the header:
            assert len(lines) - 1 == IDLE_LOG_CAPACITY + LOG_BUFFER_SIZE

    @pytest.mark.parametrize(
        (
            "context_packets",
            "servo_packet",
            "imu_data_packets",
            "processor_data_packets",
            "apogee_predictor_data_packets",
        ),
        [
            (
                (
                    make_context_data_packet(state_letter="S"),
                    make_context_data_packet(state_letter="M"),
                ),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_raw_data_packet()]),
                [],
                [],
            ),
            (
                (
                    make_context_data_packet(state_letter="S"),
                    make_context_data_packet(state_letter="M"),
                ),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [make_apogee_predictor_data_packet()],
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_log_buffer_reset_after_standby(
        self,
        logger,
        context_packets: tuple[ContextDataPacket, ContextDataPacket],
        servo_packet: ServoDataPacket,
        imu_data_packets: deque[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packets: ApogeePredictorDataPacket,
    ):
        """Tests if the buffer is logged when switching from standby to motor burn and that the
        counter is reset."""
        # Note: We are not monkeypatching the stop method here, because we want to test if the
        # entire buffer is logged when we switch from Standby to MotorBurn.
        logger.start()
        # Log more than IDLE_LOG_CAPACITY packets to test if it stops logging after hitting that.
        logger.log(
            context_packets[0],
            servo_packet,
            imu_data_packets * (IDLE_LOG_CAPACITY + 10),
            processor_data_packets * (IDLE_LOG_CAPACITY + 10),
            apogee_predictor_data_packets,
        )
        time.sleep(0.1)  # Give the process time to log to file

        # Since we did +10 above, we should have 10 left in the buffer
        assert len(logger._log_buffer) == 10
        # Let's test that switching to MotorBurn will log those packets:

        logger.log(
            context_packets[1],
            servo_packet,
            imu_data_packets * 8,
            processor_data_packets * 8,
            apogee_predictor_data_packets,
        )
        assert len(logger._log_buffer) == 0
        logger.stop()
        assert len(logger._log_buffer) == 0

        # Read the file and check if we have LOG_BUFFER_SIZE + 10
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            prev_state_vals = []  # store the log buffer values
            next_state_vals = []  # get the next state values
            for idx, val in enumerate(reader):
                count = idx
                if idx + 1 > IDLE_LOG_CAPACITY:
                    state = val["state_letter"]
                    if state == "S":
                        prev_state_vals.append(True)
                    if state == "M":
                        next_state_vals.append(True)
            assert len(logger._log_buffer) == 0
            assert len(prev_state_vals) == 10
            assert len(next_state_vals) == 8
            # First row index is zero, hence the +1
            assert count + 1 == IDLE_LOG_CAPACITY + 10 + 8

    @pytest.mark.parametrize(
        (
            "context_packet",
            "servo_packet",
            "imu_data_packets",
            "processor_data_packets",
            "apogee_predictor_data_packets",
        ),
        [
            (
                make_context_data_packet(state_letter="L"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_raw_data_packet()]),
                [],
                [],
            ),
            (
                make_context_data_packet(state_letter="L"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_log_buffer_reset_after_landed(
        self,
        logger,
        context_packet: tuple[ContextDataPacket, ContextDataPacket],
        servo_packet: ServoDataPacket,
        imu_data_packets: deque[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packets: ApogeePredictorDataPacket,
    ):
        """Tests if we've hit the idle log capacity when are in LandedState and that it is
        logged."""

        # Note: We are not monkeypatching the stop method here, because we want to test if the
        # entire buffer is logged when we are in LandedState and when stop() is called.
        logger.start()
        # Log more than IDLE_LOG_CAPACITY packets to test if it stops logging after adding on to
        # that.
        logger.log(
            context_packet,
            servo_packet,
            imu_data_packets * (IDLE_LOG_CAPACITY + 100),
            processor_data_packets * (IDLE_LOG_CAPACITY + 100),
            apogee_predictor_data_packets,
        )
        time.sleep(0.1)
        assert len(logger._log_buffer) == 100
        logger.stop()  # Will log the buffer
        assert len(logger._log_buffer) == 0

        # Read the file and check if we have exactly IDLE_LOG_CAPACITY packets
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, _ in enumerate(reader):
                count = idx

            # First row index is zero, hence the +1
            assert count + 1 == IDLE_LOG_CAPACITY + 100
            # We don't reset the log counter after stop() is called:
            assert logger._log_counter == IDLE_LOG_CAPACITY

    @pytest.mark.parametrize(
        (
            "context_packet",
            "servo_packet",
            "imu_data_packets",
            "processor_data_packets",
            "apogee_predictor_data_packet",
            "expected_outputs",
        ),
        [
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.1"),
                deque([make_raw_data_packet()]),
                [],
                [],
                [
                    LoggerDataPacket(
                        **asdict(make_context_data_packet(state_letter="S")),
                        **asdict(make_servo_data_packet(set_extension="0.1")),
                        **asdict(make_raw_data_packet()),
                    )
                ],
            ),
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.1"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                [
                    LoggerDataPacket(
                        **asdict(make_context_data_packet(state_letter="S")),
                        **asdict(make_servo_data_packet(set_extension="0.1")),
                        **asdict(make_est_data_packet()),
                        **only_logged_pdp_fields(asdict(make_processor_data_packet())),
                    ),
                ],
            ),
            (
                make_context_data_packet(state_letter="M"),
                make_servo_data_packet(set_extension="0.1"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                [
                    LoggerDataPacket(
                        **asdict(make_context_data_packet(state_letter="M")),
                        **asdict(make_servo_data_packet(set_extension="0.1")),
                        **asdict(make_raw_data_packet()),
                    ),
                    LoggerDataPacket(
                        **asdict(make_context_data_packet(state_letter="M")),
                        **asdict(make_servo_data_packet(set_extension="0.1")),
                        **asdict(make_est_data_packet()),
                        **only_logged_pdp_fields(asdict(make_processor_data_packet())),
                    ),
                ],
            ),
            (
                make_context_data_packet(state_letter="C"),
                make_servo_data_packet(set_extension="0.5"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [make_apogee_predictor_data_packet()],
                [
                    LoggerDataPacket(
                        **asdict(make_context_data_packet(state_letter="C")),
                        **asdict(make_servo_data_packet(set_extension="0.5")),
                        **asdict(make_raw_data_packet()),
                        **asdict(make_apogee_predictor_data_packet()),
                    ),
                    LoggerDataPacket(
                        **asdict(make_context_data_packet(state_letter="C")),
                        **asdict(make_servo_data_packet(set_extension="0.5")),
                        **asdict(make_est_data_packet()),
                        **only_logged_pdp_fields(asdict(make_processor_data_packet())),
                    ),
                ],
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
            "both in motor burn",
            "both in coast",
        ],
    )
    def test_prepare_logger_packets(
        self,
        logger,
        context_packet,
        servo_packet,
        imu_data_packets,
        processor_data_packets,
        apogee_predictor_data_packet,
        expected_outputs,
    ):
        """Tests whether the _prepare_logger_packets method creates correct LoggerDataPackets."""

        # set some invalid fields to test if they stay as a list
        invalid_field = ["something", "hey"]
        for imu_packet in imu_data_packets:
            imu_packet.invalid_fields = invalid_field
        # we need to change the output also
        for expected in expected_outputs:
            expected.invalid_fields = invalid_field

        # Now let's test the method
        logger_data_packets = logger._prepare_logger_packets(
            context_packet,
            servo_packet,
            imu_data_packets,
            processor_data_packets,
            apogee_predictor_data_packet,
        )
        # Check that we log every packet:
        assert len(logger_data_packets) == len(expected_outputs)

        for logger_data_packet, expected in zip(logger_data_packets, expected_outputs, strict=True):
            assert isinstance(logger_data_packet, LoggerDataPacket)
            assert logger_data_packet == expected

    @pytest.mark.parametrize(
        ("num_packets", "expected_flush_calls", "expected_lines_in_file"),
        [
            (NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING // 3, 0, 0),  # Below threshold, no flush
            (
                NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
                1,
                NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
            ),  # At threshold, one flush
            (
                NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING + 5,
                1,
                NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
            ),  # Above threshold, still one flush
            (
                2 * NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
                2,
                2 * NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
            ),  # Two flush cycles
        ],
        ids=[
            "below_flush_threshold",
            "at_flush_threshold",
            "above_flush_threshold",
            "two_flush_cycles",
        ],
    )
    def test_flush_called_with_monkeypatch(
        self,
        threaded_logger,
        num_packets: int,
        expected_flush_calls: int,
        expected_lines_in_file,
        monkeypatch,
    ):
        """
        Tests that the logger calls flush() every x lines by monkeypatching the file object's
        flush method.
        """
        # Prepare sample data packets
        context_packet = make_context_data_packet(state_letter="M")  # Avoid buffering
        servo_packet = make_servo_data_packet(set_extension="0.0")
        imu_data_packets = deque([make_raw_data_packet()])

        flush_calls = 0
        # Monkeypatch Path.open to return our custom TextIOWrapper
        original_open = threaded_logger.log_path.open

        def some_flush(original_flush):
            nonlocal flush_calls
            flush_calls += 1
            original_flush()

        def mocked_open(*args, **kwargs):
            # Call the original open with all keyword arguments
            file = original_open(**kwargs)
            original_flush = file.flush
            file.flush = partial(some_flush, original_flush)
            return file

        monkeypatch.setattr(threaded_logger.log_path.__class__, "open", mocked_open)

        # Reinitialize logger to use the monkeypatched open
        threaded_logger.start()
        assert threaded_logger.is_running

        # Log the specified number of packets
        for _ in range(num_packets):
            threaded_logger.log(
                context_packet,
                servo_packet,
                imu_data_packets.copy(),
                processor_data_packets=[],
                apogee_predictor_data_packets=[],
            )

        # Give the process time to process the queue
        time.sleep(0.1)

        # Verify the number of flush calls before stop():
        assert flush_calls == expected_flush_calls, (
            f"Expected {expected_flush_calls} flush calls, got {flush_calls}"
        )

        # Verify the number of lines in the file before stop():

        # This might be higher than expected_lines_in_file because:
        # 1. io.DEFAULT_BUFFER_SIZE is 8192 bytes, which means if more than 8192 bytes are written
        # to the file, the data will automatically be flushed to the file, calling
        # BufferedWriter.flush() instead of TextIOWrapper.flush(). This is why the number of
        # flush_calls is not changed.
        # 2. The current test setup, truncation, fields logged, etc give one row of RawDataPacket
        # as 254 bytes. This means that the file will be flushed after 8192 / 254 ~= 32 packets.
        # This is why the test case is doing a // 3 (i.e. 100 // 3), and why it works for that case.
        # 3. So as it turns out the flush() we do is actually totally unnecessary, because the file
        # is flushed automatically by the BufferedWriter much more often than we do it manually.
        with threaded_logger.log_path.open() as f:
            lines = f.readlines()
            num_data_lines = len(lines) - 1  # Subtract header
            assert num_data_lines >= expected_lines_in_file, (
                f"Expected {expected_lines_in_file} lines or more, got {num_data_lines}"
            )

        # Stop the logger cleanly to ensure all data is processed
        threaded_logger.stop()
        assert not threaded_logger.is_running

        # Verify all packets are written
        with threaded_logger.log_path.open() as f:
            lines = f.readlines()
            num_data_lines = len(lines) - 1  # Subtract header
            assert num_data_lines == num_packets, (
                f"Expected {num_packets} lines, got {num_data_lines}"
            )

    def test_benchmark_log_method(self, benchmark, logger):
        """Tests the performance of the _prepare_logger_packets method."""
        context_packet = make_context_data_packet(state_letter="S")
        servo_packet = make_servo_data_packet(set_extension="0.1")
        imu_data_packets = deque([make_raw_data_packet()])
        processor_data_packets = []
        apogee_predictor_data_packet = [make_apogee_predictor_data_packet()]

        benchmark(
            logger.log,
            context_packet,
            servo_packet,
            imu_data_packets,
            processor_data_packets,
            apogee_predictor_data_packet,
        )

    def test_benchmark_prepare_logger_packets(self, benchmark, logger):
        """Tests the performance of the _prepare_logger_packets method."""
        context_packet = make_context_data_packet(state_letter="S")
        servo_packet = make_servo_data_packet(set_extension="0.1")
        imu_data_packets = deque([make_raw_data_packet()])
        processor_data_packets = []
        apogee_predictor_data_packet = [make_apogee_predictor_data_packet()]

        benchmark(
            logger._prepare_logger_packets,
            context_packet,
            servo_packet,
            imu_data_packets,
            processor_data_packets,
            apogee_predictor_data_packet,
        )
