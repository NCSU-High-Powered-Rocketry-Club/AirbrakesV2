import csv
import multiprocessing
import multiprocessing.sharedctypes
import signal
import time

import pytest

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from airbrakes.data_handling.logger import Logger
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import LOG_CAPACITY_AT_STANDBY, STOP_SIGNAL
from tests.conftest import LOG_PATH


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
            reader = csv.reader(f)
            headers = next(reader)  # Gets the first row, which are the headers
            assert tuple(headers) == LoggedDataPacket.__struct_fields__

    def test_logging_loop_start_stop(self, logger):
        logger.start()
        assert logger.is_running

        logger.stop()
        assert not logger.is_running
        assert logger._log_process.exitcode == 0

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

    def test_logger_context_manager_with_exception(self, monkeypatch):
        """Tests whether the Logger context manager propogates unknown exceptions."""
        values = multiprocessing.Queue()

        def _logging_loop(self):
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
        test_log = {"state": "state", "extension": "0.0", "timestamp": "4"}
        logger._log_queue.put(test_log)
        assert logger._log_queue.qsize() == 1
        logger.start()
        time.sleep(0.05)  # Give the process time to log to file
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert tuple(headers) == LoggedDataPacket.__struct_fields__
            row: list[str] = next(reader)
            # create dictionary from headers (field names) and row (values)
            row_dict = dict(zip(LoggedDataPacket.__struct_fields__, row, strict=False))
            # Only fetch non-empty values:
            row_dict = {k: v for k, v in row_dict.items() if v}

            assert row_dict == test_log

    # This decorator is used to run the same test with different data
    # read more about it here: https://docs.pytest.org/en/stable/parametrize.html
    @pytest.mark.parametrize(
        "data_packet",
        [
            LoggedDataPacket(*("1" for _ in range(len(LoggedDataPacket.__struct_fields__)))),
        ],
        ids=[
            "RawDataPacket",
        ],
    )
    def test_log_method(self, logger, data_packet):
        """Tests whether the log method logs the data correctly to the CSV file."""
        logger.start()
        logger.log([data_packet])
        time.sleep(0.01)  # Give the process time to log to file
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert tuple(headers) == LoggedDataPacket.__struct_fields__

            # The row with the data packet:
            row: list[str] = next(reader)
            # create dictionary from headers (field names) and row (values)
            row_dict = dict(zip(LoggedDataPacket.__struct_fields__, row, strict=False))
            # Only fetch non-empty values:
            row_dict = {k: v for k, v in row_dict.items() if v}

            processed_data_packet_fields = list(ProcessedDataPacket.__struct_fields__)

            assert row_dict == {
                "state": "1",
                "extension": "1",
                **{attr: getattr(data_packet, attr) for attr in RawDataPacket.__struct_fields__},
                **{attr: str(getattr(data_packet, attr)) for attr in EstimatedDataPacket.__struct_fields__},
                **{attr: str(getattr(data_packet, attr)) for attr in processed_data_packet_fields},
            }

    def test_log_buffer_exceeded_standby(self, logger):
        """Tests whether the log buffer works correctly for the Standby and Landed state."""

        # Test if the buffer works correctly
        logger.start()
        log_packet = LoggedDataPacket(
            state="S",
            extension=0.0,
            timestamp=0.0,
        )
        log_packets = [log_packet for _ in range(LOG_CAPACITY_AT_STANDBY + 10)]
        # Log more than LOG_BUFFER_SIZE packets to test if it stops logging after LOG_BUFFER_SIZE.
        logger.log(log_packets)

        time.sleep(0.1)  # Give the process time to log to file
        assert len(logger._log_buffer) == 10  # Since we did +10 above, we should have 10 left in the buffer
        logger.stop()  # We must stop because otherwise the values are not flushed to the file

        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, _ in enumerate(reader):
                count = idx

            # First row is headers
            assert count + 1 == LOG_CAPACITY_AT_STANDBY
            assert logger._log_counter == LOG_CAPACITY_AT_STANDBY

    def test_log_buffer_reset_after_standby(self, logger):
        """Tests if the buffer is logged after Standby state and the counter is reset."""
        logger.start()
        log_packet = LoggedDataPacket(
            state="S",
            extension=0.0,
            timestamp=0.0,
        )
        log_packets = [log_packet for _ in range(LOG_CAPACITY_AT_STANDBY + 10)]
        # Log more than LOG_BUFFER_SIZE packets to test if it stops logging after LOG_BUFFER_SIZE.
        logger.log(log_packets)
        time.sleep(0.1)  # Give the process time to log to file
        assert len(logger._log_buffer) == 10  # Since we did +10 above, we should have 10 left in the buffer

        log_packets = [
            LoggedDataPacket(
                state="M",
                extension=0.0,
                timestamp=0.0,
            )
            for _ in range(8)
        ]

        # Let's test that switching to MotorBurn will log those packets:

        logger.log(log_packets)

        logger.stop()

        # Read the file and check if we have LOG_BUFFER_SIZE + 10
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            prev_state_vals = []  # store the log buffer values
            next_state_vals = []  # get the next state values
            for idx, val in enumerate(reader):
                count = idx
                if idx + 1 > LOG_CAPACITY_AT_STANDBY:
                    state = val["state"]
                    if state == "S":
                        prev_state_vals.append(True)
                    if state == "M":
                        next_state_vals.append(True)
            # First row is headers
            assert count + 1 == LOG_CAPACITY_AT_STANDBY + 10 + 8
            assert len(prev_state_vals) == 10
            assert len(next_state_vals) == 8

    def test_log_buffer_reset_after_landed(self, logger):
        logger.start()
        log_packet = LoggedDataPacket(
            state="L",
            extension=0.0,
            timestamp=0.0,
        )
        log_packets = [log_packet for _ in range(LOG_CAPACITY_AT_STANDBY + 100)]
        # Log more than LOG_BUFFER_SIZE packets to test if it stops logging after LOG_CAPACITY_AT_STANDBY.
        logger.log(log_packets)
        time.sleep(0.1)
        logger.stop()

        # Read the file and check if we have LOG_BUFFER_SIZE packets
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, _ in enumerate(reader):
                count = idx

            # First row is headers
            assert count + 1 == LOG_CAPACITY_AT_STANDBY
            assert logger._log_counter == LOG_CAPACITY_AT_STANDBY
