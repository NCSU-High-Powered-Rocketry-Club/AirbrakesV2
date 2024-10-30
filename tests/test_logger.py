import csv
import multiprocessing
import multiprocessing.sharedctypes
import signal
import time
from collections import deque
from typing import Literal

import msgspec
import pytest

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from airbrakes.data_handling.logger import Logger
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import IDLE_LOG_CAPACITY, LOG_BUFFER_SIZE, STOP_SIGNAL
from tests.conftest import LOG_PATH


def gen_data_packet(kind: Literal["est", "raw", "processed"]) -> IMUDataPacket | ProcessedDataPacket:
    """Generates a dummy data packet with all the values pre-filled."""
    if kind == "est":
        return EstimatedDataPacket(**{k: 1.12345678 for k in EstimatedDataPacket.__struct_fields__})
    if kind == "raw":
        return RawDataPacket(**{k: 1.98765432 for k in RawDataPacket.__struct_fields__})
    return ProcessedDataPacket(**{k: 1.88776655 for k in ProcessedDataPacket.__struct_fields__})


def patched_stop(self):
    """Monkeypatched stop method which does not log the buffer."""
    # Make sure the rest of the code is the same as the original method!
    self._log_queue.put(STOP_SIGNAL)
    self._log_process.join()


class TestLogger:
    """Tests the Logger() class in logger.py"""

    @pytest.fixture(autouse=True)  # autouse=True means run this function before/after every test
    def clear_directory(self):
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
        assert isinstance(logger._log_queue, multiprocessing.queues.Queue)
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
            assert tuple(keys) == LoggedDataPacket.__struct_fields__

    def test_log_buffer_is_full_property(self, logger):
        """Tests whether the property is_log_buffer_full works correctly."""
        assert not logger.is_log_buffer_full
        logger._log_buffer.extend([1] * (LOG_BUFFER_SIZE - 1))
        assert not logger.is_log_buffer_full
        logger._log_buffer.clear()
        assert len(logger._log_buffer) == 0
        logger._log_buffer.extend([1] * LOG_BUFFER_SIZE)
        assert logger.is_log_buffer_full

    def test_logging_loop_start_stop(self, logger):
        logger.start()
        assert logger.is_running

        logger.stop()
        assert not logger.is_running
        assert logger._log_process.exitcode == 0

    def test_logger_stop_logs_the_buffer(self, logger):
        logger.start()
        log_dict = {"state": "S", "extension": "0.0", "timestamp": "4", "invalid_fields": "[]"}
        logger._log_buffer.appendleft(log_dict)
        logger.stop()
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, row in enumerate(reader):
                count = idx + 1
                assert len(row) > 5  # Should have other fields with empty values
                # Only fetch non-empty values:
                row_dict = {k: v for k, v in row.items() if v}
                assert row_dict == log_dict
            assert count == 1

    def test_logger_ctrl_c_handling(self, monkeypatch):
        """Tests whether the Logger handles Ctrl+C events from main loop correctly."""
        values = multiprocessing.Queue()

        def _logging_loop(self):
            """Monkeypatched method for testing."""
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            while True:
                a = self._log_queue.get()
                if a == STOP_SIGNAL:
                    break
            values.put("clean exit")

        monkeypatch.setattr(Logger, "_logging_loop", _logging_loop)

        logger = Logger(LOG_PATH)
        logger.start()
        assert logger.is_running
        try:
            raise KeyboardInterrupt  # send a KeyboardInterrupt to test __exit__
        except KeyboardInterrupt:
            logger.stop()

        assert not logger.is_running
        assert not logger._log_process.is_alive()
        assert values.qsize() == 1
        assert values.get() == "clean exit"

    def test_logger_loop_exception_raised(self, monkeypatch):
        """Tests whether the Logger loop properly propogates unknown exceptions."""
        values = multiprocessing.Queue()

        def _logging_loop(_):
            """Monkeypatched method for testing."""
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            while True:
                values.put("error in loop")
                raise ValueError("some error")

        monkeypatch.setattr(Logger, "_logging_loop", _logging_loop)

        logger = Logger(LOG_PATH)
        logger.start()
        with pytest.raises(ValueError, match="some error") as excinfo:
            logger._logging_loop()

        logger.stop()
        assert not logger.is_running
        assert not logger._log_process.is_alive()
        assert values.qsize() == 2
        assert values.get() == "error in loop"
        assert "some error" in str(excinfo.value)

    def test_logging_loop_add_to_queue(self, logger):
        test_log = {"state": "state", "extension": "0.0", "timestamp": "4", "invalid_fields": "[]"}
        logger._log_queue.put(test_log)
        assert logger._log_queue.qsize() == 1
        logger.start()
        time.sleep(0.01)  # Give the process time to log to file
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert tuple(headers) == LoggedDataPacket.__struct_fields__
            for row in reader:
                row: dict[str]
            # Only fetch non-empty values:
            row_dict = {k: v for k, v in row.items() if v}

            assert row_dict == test_log

    # This decorator is used to run the same test with different data
    # read more about it here: https://docs.pytest.org/en/stable/parametrize.html
    @pytest.mark.parametrize(
        ("state", "extension", "imu_data_packets", "processed_data_packets", "predicted_apogee"),
        [
            ("S", 0.0, deque([gen_data_packet("raw")]), deque([]), 0.0),
            ("S", 0.0, deque([gen_data_packet("est")]), deque([gen_data_packet("processed")]), 1800.0),
            (
                "M",
                0.5,
                deque([gen_data_packet("raw"), gen_data_packet("est")]),
                deque([gen_data_packet("processed")]),
                1800.0,
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
            "BothDataPackets",
        ],
    )
    def test_log_method(self, logger, state, extension, imu_data_packets, processed_data_packets, predicted_apogee):
        """Tests whether the log method logs the data correctly to the CSV file."""
        logger.start()

        logger.log(state, extension, imu_data_packets.copy(), processed_data_packets.copy(), predicted_apogee)
        time.sleep(0.01)  # Give the process time to log to file
        logger.stop()

        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            assert tuple(headers) == LoggedDataPacket.__struct_fields__

            processed_data_packet_fields = {"current_altitude", "vertical_velocity", "vertical_acceleration"}
            # The row with the data packet:
            row: dict[str, str]
            for idx, row in enumerate(reader):
                # Only fetch non-empty values:
                row_dict_non_empty = {k: v for k, v in row.items() if v}
                is_est_data_packet = isinstance(imu_data_packets[idx], EstimatedDataPacket)

                assert len(row_dict_non_empty) > 10  # Random check to make sure we aren't missing any fields
                assert row == {
                    "state": state,
                    "extension": str(extension),
                    "predicted_apogee": f"{predicted_apogee:.8f}",
                    **{attr: str(getattr(imu_data_packets[idx], attr, "")) for attr in RawDataPacket.__struct_fields__},
                    **{
                        attr: str(getattr(imu_data_packets[idx], attr, ""))
                        for attr in EstimatedDataPacket.__struct_fields__
                    },
                    **{
                        attr: str(getattr(processed_data_packets[0] if is_est_data_packet else None, attr, ""))
                        for attr in processed_data_packet_fields
                    },
                }

    @pytest.mark.parametrize(
        ("state", "extension", "imu_data_packets", "processed_data_packets", "predicted_apogee"),
        [
            ("S", 0.0, deque([gen_data_packet("raw")]), deque([]), 0.0),
            ("S", 0.0, deque([gen_data_packet("est")]), deque([gen_data_packet("processed")]), 1800.0),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_log_capacity_exceeded_standby(
        self, state, extension, imu_data_packets, processed_data_packets, predicted_apogee, monkeypatch
    ):
        """Tests whether the log buffer works correctly for the Standby and Landed state."""

        monkeypatch.setattr(Logger, "stop", patched_stop)
        logger = Logger(LOG_PATH)
        # Test if the buffer works correctly
        logger.start()
        # Log more than LOG_BUFFER_SIZE packets to test if it stops logging after LOG_BUFFER_SIZE.
        logger.log(
            state,
            extension,
            imu_data_packets * (IDLE_LOG_CAPACITY + 10),
            processed_data_packets * (IDLE_LOG_CAPACITY + 10),
            predicted_apogee,
        )

        time.sleep(0.1)  # Give the process time to log to file
        assert len(logger._log_buffer) == 10  # Since we did +10 above, we should have 10 left in the buffer
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
        ("states", "extension", "imu_data_packets", "processed_data_packets", "predicted_apogee"),
        [
            (("S", "M"), 0.0, deque([gen_data_packet("raw")]), deque([]), 0.0),
            (("S", "M"), 0.0, deque([gen_data_packet("est")]), deque([gen_data_packet("processed")]), 1800.0),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_log_buffer_reset_after_standby(
        self,
        logger,
        states: tuple[str],
        extension: float,
        imu_data_packets: list[IMUDataPacket],
        processed_data_packets: list[ProcessedDataPacket],
        predicted_apogee: float,
    ):
        """Tests if the buffer is logged when switching from standby to motor burn and that the counter is reset."""
        # Note: We are not monkeypatching the stop method here, because we want to test if the entire
        # buffer is logged when we switch from Standby to MotorBurn. Monkeypatching stop() has no
        # effect on this test.
        logger.start()
        # Log more than IDLE_LOG_CAPACITY packets to test if it stops logging after hitting that.
        logger.log(
            states[0],
            extension,
            imu_data_packets * (IDLE_LOG_CAPACITY + 10),
            processed_data_packets * (IDLE_LOG_CAPACITY + 10),
            predicted_apogee,
        )
        time.sleep(0.1)  # Give the process time to log to file
        assert len(logger._log_buffer) == 10  # Since we did +10 above, we should have 10 left in the buffer

        # Let's test that switching to MotorBurn will log those packets:

        logger.log(states[1], extension, imu_data_packets * 8, processed_data_packets * 8, predicted_apogee)
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
                    states = val["state"]
                    if states == "S":
                        prev_state_vals.append(True)
                    if states == "M":
                        next_state_vals.append(True)
            assert len(logger._log_buffer) == 0
            assert len(prev_state_vals) == 10
            assert len(next_state_vals) == 8
            # First row index is zero, hence the +1
            assert count + 1 == IDLE_LOG_CAPACITY + 10 + 8

    @pytest.mark.parametrize(
        ("state", "extension", "imu_data_packets", "processed_data_packets", "predicted_apogee"),
        [
            ("L", 0.0, deque([gen_data_packet("raw")]), deque([]), 0.0),
            ("L", 0.0, deque([gen_data_packet("est")]), deque([gen_data_packet("processed")]), 1800.0),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_log_buffer_reset_after_landed(
        self, logger, state, extension, imu_data_packets, processed_data_packets, predicted_apogee
    ):
        """Tests if we've hit the idle log capacity when are in LandedState and that it is logged."""

        # Note: We are not monkeypatching the stop method here, because we want to test if the entire
        # buffer is logged when we are in LandedState and when stop() is called.
        logger.start()
        # Log more than IDLE_LOG_CAPACITY packets to test if it stops logging after adding on to that.
        logger.log(
            state,
            extension,
            imu_data_packets * (IDLE_LOG_CAPACITY + 100),
            processed_data_packets * (IDLE_LOG_CAPACITY + 100),
            predicted_apogee,
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
        ("state", "extension", "imu_data_packets", "processed_data_packets", "expected_output"),
        [
            (
                "S",
                0.1,
                deque([gen_data_packet("raw")]),
                deque([]),
                [
                    {
                        "state": "S",
                        "extension": "0.1",
                        **{k: "1.98765432" for k in RawDataPacket.__struct_fields__},
                        "predicted_apogee": "1800.00000000",
                    }
                ],
            ),
            (
                "S",
                0.1,
                deque([gen_data_packet("est")]),
                deque([gen_data_packet("processed")]),
                [
                    {
                        "state": "S",
                        "extension": "0.1",
                        **{k: "1.12345678" for k in EstimatedDataPacket.__struct_fields__},
                        **{k: "1.88776655" for k in ProcessedDataPacket.__struct_fields__},
                        "predicted_apogee": "1800.00000000",
                    }
                ],
            ),
        ],
        ids=[
            "RawDataPacket",
            "EstimatedDataPacket",
        ],
    )
    def test_create_logged_data_packets(
        self, logger, state, extension, imu_data_packets, processed_data_packets, expected_output
    ):
        """Tests whether the _create_logged_data_packets method creates the correct LoggedDataPacket objects."""

        # set some invalid fields to test if they stay as a list
        invalid_field = ["something"]
        for imu_packet in imu_data_packets:
            imu_packet.invalid_fields = invalid_field
        expected_output[0]["invalid_fields"] = invalid_field  # we need to change the output also

        logged_data_packets = logger._create_logged_data_packets(
            state, extension, imu_data_packets, processed_data_packets, 1800.0
        )
        assert len(logged_data_packets) == len(expected_output)

        for logged_data_packet, expected in zip(logged_data_packets, expected_output, strict=True):
            assert isinstance(logged_data_packet, LoggedDataPacket)
            # we will convert the logged_data_packet to a dict and compare only the non-None values
            converted = {k: v for k, v in msgspec.structs.asdict(logged_data_packet).items() if v}
            is_raw_data_packet = converted.get("scaledAccelX", False)
            # certain fields are not converted to strings (intentionally. See logged_data_packet.py)
            assert isinstance(converted["invalid_fields"], list)
            assert isinstance(converted["timestamp"], float)
            if not is_raw_data_packet:
                assert isinstance(converted["vertical_velocity"], str)
                assert isinstance(converted["current_altitude"], str)
            assert isinstance(converted["extension"], float)

            # convert the above fields for easy assertion check at the end:
            converted["timestamp"] = str(converted["timestamp"])
            if not is_raw_data_packet:
                converted["velocity"] = str(converted["vertical_velocity"])
                converted["current_altitude"] = str(converted["current_altitude"])
            converted["extension"] = str(converted["extension"])

            assert converted == expected
