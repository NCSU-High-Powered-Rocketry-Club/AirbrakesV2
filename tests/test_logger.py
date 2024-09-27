import csv
import multiprocessing
import multiprocessing.sharedctypes
import signal
import time

import pytest

from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from airbrakes.data_handling.logger import Logger
from constants import STOP_SIGNAL
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
            assert headers == LoggedDataPacket.__struct_fields__

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
            assert headers == LoggedDataPacket.__struct_fields__
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
            # Initialize RawDataPacket and EstimatedDataPacket with all dummy values
            RawDataPacket(*("2" for _ in range(len(RawDataPacket.__struct_fields__)))),
            EstimatedDataPacket(*("3" for _ in range(len(EstimatedDataPacket.__struct_fields__)))),
        ],
        ids=["RawDataPacket", "EstimatedDataPacket"],
    )
    def test_log_method(self, logger, data_packet):
        """Tests whether the log method logs the data correctly to the CSV file."""
        logger.start()
        data_processor = IMUDataProcessor([])
        logger.log(state="state", extension="0.1", imu_data_list=[data_packet], data_processor=data_processor)
        time.sleep(0.01)  # Give the process time to log to file
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == LoggedDataPacket.__struct_fields__

            # The row with the data packet:
            row: list[str] = next(reader)
            # create dictionary from headers (field names) and row (values)
            row_dict = dict(zip(LoggedDataPacket.__struct_fields__, row, strict=False))
            # Only fetch non-empty values:
            row_dict = {k: v for k, v in row_dict.items() if v}

            # assert row_dict == {
            #     "state": "state",
            #     "extension": "0.1",
            #     **{attr: getattr(data_packet, attr) for attr in data_packet.__struct_fields__},
            #     **{attr: str(getattr(data_processor, attr)) for attr in get_imu_data_processor_public_properties()},
            # }
