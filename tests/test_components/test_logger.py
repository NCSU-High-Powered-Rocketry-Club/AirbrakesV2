import csv
import queue
import threading
import time
from functools import partial
from typing import TYPE_CHECKING

import pytest
from msgspec.structs import asdict

from airbrakes.constants import (
    IDLE_LOG_CAPACITY,
    LOG_BUFFER_SIZE,
    NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
    STOP_SIGNAL,
    ServoExtension,
)
from airbrakes.data_handling.logger import Logger
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.state import (
    CoastState,
    LandedState,
    MotorBurnState,
    StandbyState,
)
from tests.auxil.utils import (
    context_packet_to_logger_kwargs,
    make_apogee_predictor_data_packet,
    make_context_data_packet,
    make_firm_data_packet,
    make_servo_data_packet,
)
from tests.conftest import LOG_PATH

if TYPE_CHECKING:
    from firm_client import FIRMDataPacket

    from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
        ApogeePredictorDataPacket,
    )
    from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
    from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


def patched_stop(self):
    """
    Monkeypatched stop method which does not log the buffer.
    """
    # Make sure the rest of the code is the same as the original method!
    self._log_queue.put(STOP_SIGNAL)
    self._log_thread.join()


def extract_state_letter(value) -> str:
    if isinstance(value, type):
        return value.__name__[0]

    if isinstance(value, str):
        if value.startswith("<class "):
            class_name = value.split(".")[-1].split("'")[0]
            return class_name[0]
        return value[0]

    return str(value)[0]


def convert_dict_vals_to_str(d: dict[str, float], truncation: bool = True) -> dict[str, str]:
    """
    Converts all values in the dictionary to strings.

    Applies truncation for floats by default. Drops None values.
    """
    new_d = {}
    for k, v in d.items():
        if isinstance(v, int):
            new_d[k] = str(v)
        elif v is None or not v:  # Skip None values
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
    """
    Modifies the Logger to run in a separate thread instead of a process.
    """
    logger = Logger(LOG_PATH)
    # Cannot use signals from child threads, so we need to monkeypatch it:
    monkeypatch.setattr("signal.signal", lambda _, __: None)
    target = threading.Thread(target=logger._logging_loop)
    logger._log_thread = target
    yield logger
    logger.stop()


class TestLogger:
    """
    Tests the Logger() class in logger.py.
    """

    sample_ldp = LoggerDataPacket(
        state_letter="S",
        set_extension="0.0",
        timestamp_seconds=4,
        retrieved_firm_packets=None,
        apogee_predictor_queue_size=None,
        update_timestamp_ns=None,
    )

    @pytest.fixture(autouse=True)  # autouse=True means run this function before/after every test
    def _clear_directory(self):
        """
        Clear the tests/logs directory after running each test.
        """
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
        assert isinstance(logger._log_queue, queue.SimpleQueue)
        assert isinstance(logger._log_thread, threading.Thread)

        # Test that the thread is not running
        assert not logger.is_running
        assert not logger._log_thread.is_alive()

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
        """
        Tests whether the property is_log_buffer_full works correctly.
        """
        assert not logger.is_log_buffer_full
        logger._log_buffer.extend([1] * (LOG_BUFFER_SIZE - 1))
        assert not logger.is_log_buffer_full
        logger._log_buffer.clear()
        assert len(logger._log_buffer) == 0
        logger._log_buffer.extend([1] * LOG_BUFFER_SIZE)
        assert logger.is_log_buffer_full

    def test_logger_stops_on_stop_signal(self, logger):
        """
        Tests whether the logger stops when it receives a stop signal.
        """
        logger.start()
        logger._log_queue.put(STOP_SIGNAL)
        time.sleep(0.4)
        assert not logger.is_running
        assert not logger._log_thread.is_alive()
        logger.stop()

    def test_logging_loop_start_stop(self, logger):
        logger.start()
        assert logger.is_running

        logger.stop()
        assert not logger.is_running

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

    def test_logging_loop_add_to_queue(self, logger):
        logger.start()
        logger._log_queue.put(self.sample_ldp)
        time.sleep(0.1)  # Give the thread time to log to file
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
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
            "firm_data_packets",
            "apogee_predictor_data_packet",
            "file_lines",
            "expected_output",
        ),
        [
            (
                make_context_data_packet(state=StandbyState),
                make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION),
                [make_firm_data_packet()],
                [],
                1,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state=StandbyState))
                        ),
                        **asdict(
                            make_servo_data_packet(
                                set_extension=str(ServoExtension.MIN_EXTENSION.value)
                            )
                        ),
                        **convert_dict_vals_to_str(make_firm_data_packet().as_dict()),
                    }
                ],
            ),
            (
                make_context_data_packet(state=StandbyState),
                make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION),
                [make_firm_data_packet()] * 2,
                [],
                2,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state=StandbyState))
                        ),
                        **asdict(
                            make_servo_data_packet(
                                set_extension=str(ServoExtension.MIN_EXTENSION.value)
                            )
                        ),
                        **convert_dict_vals_to_str(make_firm_data_packet().as_dict()),
                    }
                ]
                * 2,
            ),
            (
                make_context_data_packet(state=MotorBurnState),
                make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION),
                [make_firm_data_packet()],
                [],
                1,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state=MotorBurnState))
                        ),
                        **asdict(
                            make_servo_data_packet(
                                set_extension=str(ServoExtension.MIN_EXTENSION.value)
                            )
                        ),
                        **convert_dict_vals_to_str(make_firm_data_packet().as_dict()),
                    }
                ],
            ),
            (
                make_context_data_packet(state=CoastState),
                make_servo_data_packet(set_extension=ServoExtension.MAX_NO_BUZZ),
                [make_firm_data_packet()],
                [],
                1,
                [
                    {
                        **convert_dict_vals_to_str(
                            asdict(make_context_data_packet(state=CoastState))
                        ),
                        **asdict(
                            make_servo_data_packet(
                                set_extension=str(ServoExtension.MAX_NO_BUZZ.value)
                            )
                        ),
                        **convert_dict_vals_to_str(make_firm_data_packet().as_dict()),
                    }
                ],
            ),
        ],
        ids=[
            "FIRMDataPacket",
            "2 FIRMDataPackets",
            "FIRMDataPacket in MotorBurn",
            "FIRMDataPacket in Coast",
        ],
    )
    def test_log_method(
        self,
        logger,
        context_packet,
        servo_packet,
        firm_data_packets,
        apogee_predictor_data_packet,
        file_lines,
        expected_output: list[dict],
    ):
        """
        Tests whether the log method logs the data correctly to the CSV file.
        """
        logger.start()

        logger.log(
            context_packet,
            servo_packet,
            firm_data_packets.copy(),
            apogee_predictor_data_packet,
        )
        time.sleep(0.01)  # Give the thread time to log to file
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

                exp = expected_output[idx].copy()
                # Replace "state" with "state_letter" so it matches the CSV output
                if "state" in exp and "state_letter" not in exp:
                    exp["state_letter"] = extract_state_letter(exp["state"])
                    exp.pop("state")

                exp = convert_dict_vals_to_str(exp, truncation=False)
                assert row_dict_non_empty == exp

            assert idx + 1 == file_lines

    def test_log_capacity_exceeded_standby(self, monkeypatch, logger):
        """
        Tests whether the log buffer works correctly for the Standby state.
        """
        # Setup packets
        context_packet = make_context_data_packet(state=StandbyState)
        servo_packet = make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION)
        firm_data_packets = [make_firm_data_packet()]
        apogee_predictor_data_packets = make_apogee_predictor_data_packet()

        monkeypatch.setattr(logger.__class__, "stop", patched_stop)

        # Test if the buffer works correctly
        logger.start()

        # Log more than IDLE_LOG_CAPACITY packets to test if it stops logging after LOG_BUFFER_SIZE.
        # We multiply lists to simulate multiple packets coming in
        logger.log(
            context_packet,
            servo_packet,
            firm_data_packets * (IDLE_LOG_CAPACITY + 10),
            apogee_predictor_data_packets,
        )

        time.sleep(0.01)  # Give the thread time to log to file

        # Since we did +10 above the capacity, we should have 10 left in the buffer
        # (The first IDLE_LOG_CAPACITY were written to disk, the rest are buffered)
        assert len(logger._log_buffer) == 10

        logger.stop()  # We must stop because otherwise the values are not flushed to the file due to monkeypatch

        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            # Count rows excluding header
            count = sum(1 for _ in reader)

        # The file should only contain the IDLE_LOG_CAPACITY rows.
        # The 10 in the buffer were never flushed because we monkeypatched stop().
        assert count == IDLE_LOG_CAPACITY
        assert logger._log_counter == IDLE_LOG_CAPACITY

    def test_log_buffer_keeps_increasing(self, logger):
        """
        Tests that the buffer keeps building up on subsequent calls to log().
        """
        # Setup packets
        context_packet = make_context_data_packet(state=StandbyState)
        servo_packet = make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION)
        firm_data_packets = [make_firm_data_packet()]
        apogee_predictor_data_packets = make_apogee_predictor_data_packet()

        logger.start()

        # 1. Fill the IDLE capacity + put 10 in buffer
        logger.log(
            context_packet,
            servo_packet,
            firm_data_packets * (IDLE_LOG_CAPACITY + 10),
            apogee_predictor_data_packets,
        )

        # 2. Log WAY more than the buffer size to test capping mechanism
        # This will attempt to add LOG_BUFFER_SIZE + 10 packets to the existing buffer.
        logger.log(
            context_packet,
            servo_packet,
            firm_data_packets * (LOG_BUFFER_SIZE + 10),
            apogee_predictor_data_packets,
        )

        time.sleep(0.01)  # Give the thread time to log to file

        # The buffer should be capped at exactly LOG_BUFFER_SIZE.
        # Any excess packets (the +10 and the previous +10) are dropped or fit within the cap.
        assert len(logger._log_buffer) == LOG_BUFFER_SIZE

        logger.stop()  # stop() will flush the buffer to disk

        assert len(logger._log_buffer) == 0

        with logger.log_path.open() as file:
            lines = file.readlines()
            # First row is the header, so we subtract 1.
            # Total lines should be:
            #   IDLE_LOG_CAPACITY (written immediately in step 1)
            # + LOG_BUFFER_SIZE (flushed from buffer in step 3)
            assert len(lines) - 1 == IDLE_LOG_CAPACITY + LOG_BUFFER_SIZE

    def test_log_buffer_reset_after_standby(self, logger):
        """
        Tests if the buffer is logged when switching from standby to motor burn and that the counter
        is reset.
        """
        # Setup packets
        context_standby = make_context_data_packet(state=StandbyState)
        context_motor = make_context_data_packet(state=MotorBurnState)
        servo_packet = make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION)

        firm_data_packets = [make_firm_data_packet()]
        apogee_predictor_data_packet = make_apogee_predictor_data_packet()

        # Note: We are not monkeypatching the stop method here, because we want to test if the
        # entire buffer is logged when we switch from Standby to MotorBurn.
        logger.start()

        # 1. Log in Standby (IDLE capacity + 10 overflow)
        # The first IDLE_LOG_CAPACITY get written immediately. The +10 sit in the buffer.
        logger.log(
            context_standby,
            servo_packet,
            firm_data_packets * (IDLE_LOG_CAPACITY + 10),
            apogee_predictor_data_packet,
        )
        time.sleep(0.1)  # Give the thread time to log to file

        # Since we did +10 above, we should have 10 left in the buffer
        assert len(logger._log_buffer) == 10

        # 2. Switch to MotorBurn -> Should flush the buffer (the previous 10) + log new ones
        logger.log(
            context_motor,
            servo_packet,
            firm_data_packets * 8,
            apogee_predictor_data_packet,
        )

        # Buffer should be empty now (flushed to disk due to state change)
        assert len(logger._log_buffer) == 0

        logger.stop()
        assert len(logger._log_buffer) == 0

        # 3. Read the file and verify correct state transition
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            prev_state_vals = []  # store the log buffer values (Standby)
            next_state_vals = []  # get the next state values (MotorBurn)

            for idx, val in enumerate(reader):
                count = idx
                # We are checking the rows that occurred AFTER the idle capacity was full
                if idx + 1 > IDLE_LOG_CAPACITY:
                    state = val["state_letter"]
                    if state == "S":
                        prev_state_vals.append(True)
                    if state == "M":
                        next_state_vals.append(True)

            # Ensure we didn't leave anything in the buffer object
            assert len(logger._log_buffer) == 0

            # We expect 10 Standby packets (the ones that were buffered)
            assert len(prev_state_vals) == 10

            # We expect 8 MotorBurn packets (the ones logged after switch)
            assert len(next_state_vals) == 8

            # Total lines = IDLE_CAPACITY + 10 buffered + 8 new
            # (count is 0-indexed, so we add 1 for total lines)
            assert count + 1 == IDLE_LOG_CAPACITY + 10 + 8

    def test_log_buffer_reset_after_landed(self, logger):
        """
        Tests if we've hit the idle log capacity when are in LandedState and that it is logged.
        """
        # Setup the specific packets for this test
        context_packet = make_context_data_packet(state=LandedState)
        servo_packet = make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION)
        firm_data_packets = [make_firm_data_packet()]
        apogee_predictor_data_packet = None

        # Note: We are not monkeypatching the stop method here, because we want to test if the
        # entire buffer is logged when we are in LandedState and when stop() is called.
        logger.start()

        # Log more than IDLE_LOG_CAPACITY packets to test if it stops logging after adding on to
        # that.
        packets_to_log = IDLE_LOG_CAPACITY + 100

        logger.log(
            context_packet,
            servo_packet,
            firm_data_packets * packets_to_log,
            apogee_predictor_data_packet,
        )

        time.sleep(0.1)

        # In LandedState, the logger typically stops incrementing the main counter
        # but might still hold overflow in the buffer until flush/stop.
        assert len(logger._log_buffer) == 100

        logger.stop()  # Will log the rest of the buffer
        assert len(logger._log_buffer) == 0

        # Read the file and check if we have exactly IDLE_LOG_CAPACITY + 100 packets
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            # Count the rows in the CSV (excluding header)
            count = sum(1 for _ in reader)

            # We expect all packets to be logged eventually
            assert count == packets_to_log

            # However, the internal log counter should have capped at IDLE_LOG_CAPACITY
            # as per LandedState logic
            assert logger._log_counter == IDLE_LOG_CAPACITY

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
        Tests that the logger calls flush() every x lines by monkeypatching the file object's flush
        method.
        """
        # Prepare sample data packets
        context_packet = make_context_data_packet(state=MotorBurnState)  # Avoid buffering
        servo_packet = make_servo_data_packet(set_extension=ServoExtension.MIN_EXTENSION)
        firm_data_packets = [make_firm_data_packet()]

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
                firm_data_packets.copy(),
                apogee_predictor_data_packet=None,
            )

        # Give the thread time to process the queue
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

    # TODO: should add these back
    # def test_benchmark_log_method(self, benchmark, logger):
    #     """
    #     Tests the performance of the _prepare_logger_packets method.
    #     """
    #     context_packet = make_context_data_packet(state=StandbyState)
    #     servo_packet = make_servo_data_packet(set_extension="0.1")
    #     firm_data_packets = [make_firm_data_packet()]
    #     apogee_predictor_data_packet = make_apogee_predictor_data_packet()
    #
    #     benchmark(
    #         logger.log,
    #         context_packet,
    #         servo_packet,
    #         firm_data_packets,
    #         apogee_predictor_data_packet,
    #     )
    #
    # def test_benchmark_prepare_logger_packets(self, benchmark, logger):
    #     """
    #     Tests the performance of the _prepare_logger_packets method.
    #     """
    #     context_packet = make_context_data_packet(state=StandbyState)
    #     servo_packet = make_servo_data_packet(set_extension="0.1")
    #     firm_data_packets = [make_firm_data_packet()]
    #     apogee_predictor_data_packet = make_apogee_predictor_data_packet()
    #
    #     benchmark(
    #         logger._prepare_logger_packets,
    #         context_packet,
    #         servo_packet,
    #         firm_data_packets,
    #         apogee_predictor_data_packet,
    #     )
