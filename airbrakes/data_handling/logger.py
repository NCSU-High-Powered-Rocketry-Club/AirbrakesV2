"""Module for logging data to a CSV file in real time."""

import contextlib
import csv
import os
import queue
import threading
from collections import deque
from typing import TYPE_CHECKING, Any, Literal

import msgspec
from msgspec.structs import asdict

from airbrakes.constants import (
    IDLE_LOG_CAPACITY,
    LOG_BUFFER_SIZE,
    NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
    STOP_SIGNAL,
)
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.state import LandedState, StandbyState
from airbrakes.utils import get_all_packets_from_queue

if TYPE_CHECKING:
    from pathlib import Path

    from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
        ApogeePredictorDataPacket,
    )
    from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
    from airbrakes.data_handling.packets.imu_data_packet import IMUDataPacket
    from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
    from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket

DecodedLoggerDataPacket = list[int | float | str]


class Logger:
    """
    A class that logs data to a CSV file.

    The logging runs in a separate thread. This is because the logging
    thread is I/O-bound, meaning that it spends most of its time waiting
    for the file to be written to. By running it in a separate thread,
    we can continue to log data while the main loop is running. It uses
    Python's csv module to append the airbrakes' current state,
    extension, and FIRM data to our logs in real time.
    """

    __slots__ = ("_log_buffer", "_log_counter", "_log_queue", "_log_thread", "log_path")

    def __init__(self, log_dir: Path) -> None:
        """
        Initializes the logger object.

        It creates a new log file in the specified directory. It creates
        a queue to store log messages, and starts a separate thread to
        handle the logging. We are logging a lot of data, and logging is
        I/O-bound, so running it in a separate thread allows the main
        loop to continue running without waiting for the log file to be
        written to.
        :param log_dir: The directory where the log files will be.
        """
        # Create the log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Get all existing log files and find the highest suffix number
        existing_logs = list(log_dir.glob("log_*.csv"))
        max_suffix = (
            max(int(log.stem.split("_")[-1]) for log in existing_logs) if existing_logs else 0
        )

        # Buffer for StandbyState and LandedState
        self._log_counter = 0

        # Create a new log file with the next number in sequence
        self._log_buffer: deque[LoggerDataPacket] = deque(maxlen=LOG_BUFFER_SIZE)
        self.log_path = log_dir / f"log_{max_suffix + 1}.csv"
        with self.log_path.open(mode="w", newline="") as file_writer:
            csv.writer(file_writer).writerow(LoggerDataPacket.__struct_fields__)

        self._log_queue: queue.SimpleQueue[LoggerDataPacket | Literal["STOP"]] = queue.SimpleQueue()

        # Start the logging thread
        self._log_thread = threading.Thread(
            target=self._logging_loop, name="Logger Thread", daemon=True
        )

    @property
    def is_running(self) -> bool:
        """Returns whether the logging thread is running."""
        return self._log_thread.is_alive()

    @property
    def is_log_buffer_full(self) -> bool:
        """Returns whether the idle-state log buffer has reached capacity."""
        return len(self._log_buffer) == LOG_BUFFER_SIZE

    @staticmethod
    def _convert_unknown_type_to_str(obj_type: Any) -> str:
        """
        Truncates the decimal place of the object to 8 decimal places.

        Used by msgspec to convert numpy float64 to a string.
        :param obj_type: The object to truncate.
        :return: The truncated object.
        """
        return f"{obj_type:.8f}"

    @staticmethod
    def _prepare_logger_packets(
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        imu_data_packets: list[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket] | None,
        apogee_predictor_data_packet: ApogeePredictorDataPacket | None,
    ) -> list[LoggerDataPacket]:
        """Create one log row for each raw or estimated IMU packet."""
        context_values = asdict(context_data_packet)
        state = context_values.pop("state")
        servo_values = asdict(servo_data_packet)
        prediction_values = (
            asdict(apogee_predictor_data_packet) if apogee_predictor_data_packet is not None else {}
        )
        processed_packets = (
            iter(processor_data_packets) if processor_data_packets is not None else iter(())
        )
        logger_packets: list[LoggerDataPacket] = []

        for imu_data_packet in imu_data_packets:
            # This way we only log the processor packets with their corresponding estimated packets
            processor_values = {}

            if isinstance(imu_data_packet, EstimatedDataPacket):
                with contextlib.suppress(StopIteration):
                    processor_values = asdict(next(processed_packets))

            logger_packets.append(
                LoggerDataPacket(
                    state_letter=state.__name__[0],
                    **servo_values,
                    **asdict(imu_data_packet),
                    **processor_values,
                    **prediction_values,
                    **context_values,
                )
            )
        return logger_packets

    def start(self) -> None:
        """
        Start the logging thread.

        This is called before the main loop starts.
        """
        self._log_thread.start()

    def stop(self) -> None:
        """
        Stops the logging thread.

        It will finish logging the current message and then stop
        """
        # Log the buffer before stoppig the thread.
        self._log_the_buffer()
        self._log_queue.put(STOP_SIGNAL)
        self._log_thread.join()

    def log(
        self,
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        imu_data_packets: list[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packet: ApogeePredictorDataPacket | None,
    ) -> None:
        """
        Logs the current state, extension, and IMU data to the CSV file.

        :param context_data_packet: The current context data packet.
        :param servo_data_packet: The current servo data packet.
        :param imu_data_packets: The current IMU data packets.
        :param processor_data_packets: The current processor data packets.
        :param apogee_predictor_data_packet: The current apogee predictor data packet
        """
        # We are populating a list within the fields of the logger data packet
        logger_packets = self._prepare_logger_packets(
            context_data_packet,
            servo_data_packet,
            imu_data_packets,
            processor_data_packets,
            apogee_predictor_data_packet,
        )

        # If we are in Standby or Landed State, we need to buffer the data packets:
        if context_data_packet.state in (StandbyState, LandedState):
            # Determine how many packets to log and buffer
            log_capacity = max(0, IDLE_LOG_CAPACITY - self._log_counter)
            to_log = logger_packets[:log_capacity]
            self._log_counter += len(to_log)
            for packet in to_log:
                self._log_queue.put(packet)
            self._log_buffer.extend(logger_packets[log_capacity:])
            return

        if self._log_buffer:
            self._log_the_buffer()

        # Reset the counter for other states
        self._log_counter = 0
        for packet in logger_packets:
            self._log_queue.put(packet)

    def _log_the_buffer(self) -> None:
        """
        Enqueues all the packets in the log buffer to the log queue, so they will be logged.
        """
        for packet in self._log_buffer:
            self._log_queue.put(packet)
        self._log_buffer.clear()

# ------------------------ ALL METHODS BELOW RUN IN A SEPARATE THREAD -------------------------

    @staticmethod
    def _truncate_floats(data: DecodedLoggerDataPacket) -> list[str | int]:
        """
        Truncates the decimal place of the floats in the list to 8 decimal
        places.

        :param data: The list of values whose floats we should truncate.
        :return: The truncated list.
        """
        return [f"{value:.8f}" if isinstance(value, float) else value for value in data]

    def _logging_loop(self) -> None:
        """
        The loop that saves data to the logs.

        It runs in parallel with the main loop.
        """
        # Set up the CSV logging in the new thread
        with self.log_path.open(mode="a", newline="") as file_writer:
            writer = csv.writer(file_writer)
            number_of_lines_logged = 0
            while True:
                # Get a message from the queue (this will block until a message is available)
                # Because theres no timeout, it will wait indefinitely until it gets a message.
                logger_packets = get_all_packets_from_queue(self._log_queue, block=True)
                packet_fields = msgspec.to_builtins(
                    logger_packets, enc_hook=Logger._convert_unknown_type_to_str
                )
                # If the message is the stop signal, break ouit of the loop.
                for message_field in packet_fields:
                    if message_field == STOP_SIGNAL:
                        return
                    writer.writerow(self._truncate_floats(message_field))
                    number_of_lines_logged += 1
                    # During our Pelicanator 1 flight, the rocket fell and had a very hard impact
                    # causing the pi to lose power. This caused us to lose a lot of lines of data
                    # that were not written to the log file. To prevent this from happening again,
                    # we flush the logger 1000 lines (equivalent to 1 second).
                    if number_of_lines_logged % NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING == 0:
                        # Tell Python to flush the data. This gives the data to the OS, and it is
                        # stored as a dirty page cache (in memory) until the OS decides to write it
                        # to disk. Technically python automatically flushes the data when the python
                        # buffer is full (8192 bytes, which would be about 25 lines of data)
                        file_writer.flush()
                        # Tell the OS to write the file to disk from the dirty page cache. This
                        # ensures that the data is written to disk and not just stored in memory.
                        # This operation is the one which is actually "blocking" when talking about
                        # file I/O.
                        os.fsync(file_writer.fileno())
