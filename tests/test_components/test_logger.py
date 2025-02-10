import csv
import multiprocessing
import multiprocessing.sharedctypes
import time
from collections import deque

import faster_fifo
import pytest
from msgspec import to_builtins

from airbrakes.constants import IDLE_LOG_CAPACITY, LOG_BUFFER_SIZE, STOP_SIGNAL
from airbrakes.telemetry.logger import Logger
from airbrakes.telemetry.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
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


def convert_dict_vals_to_str(d: dict[str, float]) -> dict[str, str]:
    """Converts all values in the dictionary to strings."""
    return {k: str(v) for k, v in d.items()}


class TestLogger:
    """Tests the Logger() class in logger.py"""

    sample_data = {
        "state_letter": "S",
        "set_extension": "0.0",
        "timestamp": "4",
        "invalid_fields": "[]",
    }

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
            assert list(keys) == list(LoggerDataPacket.__annotations__)

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
        logger._log_buffer.appendleft(self.sample_data)
        logger.stop()
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            count = 0
            for idx, row in enumerate(reader):
                count = idx + 1
                assert len(row) > 5  # Should have other fields with empty values
                # Only fetch non-empty values:
                row_dict = {k: v for k, v in row.items() if v}
                assert row_dict == self.sample_data
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

    def test_logger_loop_exception_raised(self, logger):
        """Tests whether the Logger loop properly propogates unknown exceptions."""
        logger._log_queue.put({"wrong_filed": "wrong_value"})
        with pytest.raises(ValueError, match="dict contains fields not in fieldnames"):
            logger._logging_loop()

    def test_logging_loop_add_to_queue(self, logger):
        logger._log_queue.put(self.sample_data)
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

            assert row_dict == self.sample_data

    def test_queue_hits_timeout_and_continues(self, logger, monkeypatch):
        """Tests whether the logger continues to log after a timeout."""
        monkeypatch.setattr("airbrakes.telemetry.logger.MAX_GET_TIMEOUT_SECONDS", 0.01)
        logger.start()
        time.sleep(0.05)
        logger._log_queue.put(self.sample_data)
        logger.stop()
        # Let's check the contents of the file:
        with logger.log_path.open() as f:
            reader = csv.DictReader(f)
            row = {}
            for row in reader:
                row: dict[str]
            # Only fetch non-empty values:
            row_dict = {k: v for k, v in row.items() if v}

            assert row_dict == self.sample_data

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
        ),
        [
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_raw_data_packet()]),
                [],
                [],
                1,
            ),
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.0"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                1,
            ),
            (
                make_context_data_packet(state_letter="M"),
                make_servo_data_packet(set_extension="0.5"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                2,
            ),
            (
                make_context_data_packet(state_letter="C"),
                make_servo_data_packet(set_extension="0.4"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [make_apogee_predictor_data_packet()],
                2,
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

            processor_data_packet_fields = {
                "current_altitude",
                "vertical_velocity",
                "vertical_acceleration",
            }
            # The row with the data packet:
            row: dict[str, str]
            idx = -1
            for idx, row in enumerate(reader):
                # Only fetch non-empty values:
                row_dict_non_empty = {k: v for k, v in row.items() if v}
                is_est_data_packet = isinstance(imu_data_packets[idx], EstimatedDataPacket)

                # Random check to make sure we aren't missing any fields
                assert len(row_dict_non_empty) > 19

                # Also checks if truncation is working correctly:
                expected_output = {
                    **convert_dict_vals_to_str(to_builtins(context_packet)),
                    **to_builtins(servo_packet),
                    **{
                        attr: f"{getattr(imu_data_packets[idx], attr, 0.0):.8f}"
                        for attr in RawDataPacket.__struct_fields__
                    },
                    **{
                        attr: f"{getattr(imu_data_packets[idx], attr, 0.0):.8f}"
                        for attr in EstimatedDataPacket.__struct_fields__
                    },
                    **{
                        attr: f"{
                            getattr(
                                processor_data_packets[0] if is_est_data_packet else None, attr, 0.0
                            ):.8f
                        }"
                        for attr in processor_data_packet_fields
                    },
                    **{k: "" for k in ApogeePredictorDataPacket.__struct_fields__},
                }
                # Convert 0.0 values:
                dropped = {k: "" for k, v in expected_output.items() if v == "0.00000000"}
                expected_output.update(dropped)

                # Add the Apogee Predictor Data Packet fields, only for the first row:
                if idx == 0 and apogee_predictor_data_packets:
                    apogee_pred_packet_dict = to_builtins(apogee_predictor_data_packets[0])
                    apogee_pred_packet_dict = Logger._truncate_floats(apogee_pred_packet_dict)
                    expected_output.update(apogee_pred_packet_dict)

                assert row == expected_output

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
    ):
        """Tests whether the log buffer works correctly for the Standby and Landed state."""

        monkeypatch.setattr(Logger, "stop", patched_stop)
        logger = Logger(LOG_PATH)
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
                    {
                        **to_builtins(make_context_data_packet(state_letter="S")),
                        **to_builtins(make_servo_data_packet(set_extension="0.1")),
                        **{k: 1.987654321 for k in RawDataPacket.__struct_fields__},
                        **remove_state_letter(to_builtins(make_context_data_packet())),
                    }
                ],
            ),
            (
                make_context_data_packet(state_letter="S"),
                make_servo_data_packet(set_extension="0.1"),
                deque([make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                [
                    {
                        **to_builtins(make_context_data_packet(state_letter="S")),
                        **to_builtins(make_servo_data_packet(set_extension="0.1")),
                        **{k: 1.123456789 for k in EstimatedDataPacket.__struct_fields__},
                        **{k: 1.887766554 for k in ProcessorDataPacket.__struct_fields__},
                        **remove_state_letter(to_builtins(make_context_data_packet())),
                    }
                ],
            ),
            (
                make_context_data_packet(state_letter="M"),
                make_servo_data_packet(set_extension="0.1"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [],
                [
                    {
                        **to_builtins(make_context_data_packet(state_letter="M")),
                        **to_builtins(make_servo_data_packet(set_extension="0.1")),
                        **{k: 1.987654321 for k in RawDataPacket.__struct_fields__},
                        **remove_state_letter(to_builtins(make_context_data_packet())),
                    },
                    {
                        **to_builtins(make_context_data_packet(state_letter="M")),
                        **to_builtins(make_servo_data_packet(set_extension="0.1")),
                        **{k: 1.123456789 for k in EstimatedDataPacket.__struct_fields__},
                        **{k: 1.887766554 for k in ProcessorDataPacket.__struct_fields__},
                    },
                ],
            ),
            (
                make_context_data_packet(state_letter="C"),
                make_servo_data_packet(set_extension="0.5"),
                deque([make_raw_data_packet(), make_est_data_packet()]),
                [make_processor_data_packet()],
                [make_apogee_predictor_data_packet()],
                [
                    {
                        **to_builtins(make_context_data_packet(state_letter="C")),
                        **to_builtins(make_servo_data_packet(set_extension="0.5")),
                        **{k: 1.987654321 for k in RawDataPacket.__struct_fields__},
                        **remove_state_letter(to_builtins(make_context_data_packet())),
                        **to_builtins(make_apogee_predictor_data_packet()),
                    },
                    {
                        **to_builtins(make_context_data_packet(state_letter="C")),
                        **to_builtins(make_servo_data_packet(set_extension="0.5")),
                        **{k: 1.123456789 for k in EstimatedDataPacket.__struct_fields__},
                        **{k: 1.887766554 for k in ProcessorDataPacket.__struct_fields__},
                    },
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
    def test_prepare_log_dict(
        self,
        logger,
        context_packet,
        servo_packet,
        imu_data_packets,
        processor_data_packets,
        apogee_predictor_data_packet,
        expected_outputs,
    ):
        """Tests whether the _prepare_log_dict method creates the correct LoggerDataPackets."""

        # set some invalid fields to test if they stay as a list
        invalid_field = ["something"]
        for imu_packet in imu_data_packets:
            imu_packet.invalid_fields = invalid_field
        # we need to change the output also
        for expected in expected_outputs:
            expected["invalid_fields"] = invalid_field

        # Now let's test the method
        logger_data_packets = logger._prepare_log_dict(
            context_packet,
            servo_packet,
            imu_data_packets,
            processor_data_packets,
            apogee_predictor_data_packet,
        )
        # Check that we log every packet:
        assert len(logger_data_packets) == len(expected_outputs)

        for logger_data_packet, expected in zip(logger_data_packets, expected_outputs, strict=True):
            assert isinstance(logger_data_packet, dict)
            converted = logger_data_packet

            # certain fields are not converted to strings (intentionally. See logger.py)
            assert isinstance(converted["invalid_fields"], list)
            assert isinstance(converted["timestamp"], float)

            # Remove "time_since_last_data_packet" from the expected output, since we don't log that
            expected.pop("time_since_last_data_packet", None)

            assert converted == expected
