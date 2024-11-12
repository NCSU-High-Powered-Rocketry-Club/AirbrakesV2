"""Module for logging data to a CSV file in real time."""

import csv
import multiprocessing
import signal
from collections import deque
from pathlib import Path
from typing import Any, Literal

from msgspec import to_builtins

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import IDLE_LOG_CAPACITY, LOG_BUFFER_SIZE, STOP_SIGNAL


class Logger:
    """
    A class that logs data to a CSV file. Similar to the IMU class, it runs in a separate process.
    This is because the logging process is I/O-bound, meaning that it spends most of its time
    waiting for the file to be written to. By running it in a separate process, we can continue to
    log data while the main loop is running.

    It uses Python's csv module to append the airbrakes' current state, extension, and IMU data to
    our logs in real time.

    :param log_dir: The directory where the log files will be.
    """

    __slots__ = ("_log_buffer", "_log_counter", "_log_process", "_log_queue", "log_path")

    def __init__(self, log_dir: Path) -> None:
        """
        Initializes the logger object. It creates a new log file in the specified directory. Like
        the IMU class, it creates a queue to store log messages, and starts a separate process to
        handle the logging. We are logging a lot of data, and logging is I/O-bound, so running it
        in a separate process allows the main loop to continue running without waiting for the log
        file to be written to.
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
        self._log_buffer = deque(maxlen=LOG_BUFFER_SIZE)

        # Create a new log file with the next number in sequence
        self.log_path = log_dir / f"log_{max_suffix + 1}.csv"
        with self.log_path.open(mode="w", newline="") as file_writer:
            writer = csv.DictWriter(file_writer, fieldnames=list(LoggedDataPacket.__annotations__))
            writer.writeheader()

        # Makes a queue to store log messages, basically it's a process-safe list that you add to
        # the back and pop from front, meaning that things will be logged in the order they were
        # added.
        # Signals (like stop) are sent as strings, but data is sent as dictionaries
        self._log_queue: multiprocessing.Queue[LoggedDataPacket | Literal["STOP"]] = (
            multiprocessing.Queue()
        )

        # Start the logging process
        self._log_process = multiprocessing.Process(
            target=self._logging_loop, name="Logger Process"
        )

    @property
    def is_running(self) -> bool:
        """
        Returns whether the logging process is running.
        """
        return self._log_process.is_alive()

    @property
    def is_log_buffer_full(self) -> bool:
        """
        Returns whether the log buffer is full.
        """
        return len(self._log_buffer) == LOG_BUFFER_SIZE

    def start(self) -> None:
        """
        Starts the logging process. This is called before the main while loop starts.
        """
        self._log_process.start()

    def stop(self) -> None:
        """
        Stops the logging process. It will finish logging the current message and then stop.
        """
        # Log the buffer before stopping the process
        self._log_the_buffer()
        self._log_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        # Waits for the process to finish before stopping it
        self._log_process.join()

    def log(
        self,
        state: str,
        extension: float,
        imu_data_packets: deque[IMUDataPacket],
        processed_data_packets: deque[ProcessedDataPacket],
        predicted_apogee: float,
    ) -> None:
        """
        Logs the current state, extension, and IMU data to the CSV file.
        :param state: The current state of the airbrakes.
        :param extension: The current extension of the airbrakes.
        :param imu_data_packets: The IMU data packets to log.
        :param processed_data_packets: The processed data packets to log.
        :param predicted_apogee: The predicted apogee of the rocket. Note: Since this is fetched
            from the apogee predictor, which runs in a separate process, it may not be the most
            recent value, nor would it correspond to the respective data packet being logged.
        """
        # We only want the first letter of the state to save space
        state_letter = state[0]
        # We are populating a dictionary with the fields of the logged data packet
        logged_data_packets: deque[LoggedDataPacket] = self._prepare_log_dict(
            state_letter,
            str(extension),
            imu_data_packets,
            processed_data_packets,
            predicted_apogee,
        )

        # Loop through all the IMU data packets
        for logged_data_packet in logged_data_packets:
            # If the state is StandbyState or LandedState, we create a buffer for data packets
            # because otherwise we could have gigabytes of data in the log file just for when the
            # rocket is on the ground.
            if state_letter in ["S", "L"]:  # S: StandbyState, L: LandedState
                if self._log_counter < IDLE_LOG_CAPACITY:
                    # add the count:
                    self._log_counter += 1
                else:
                    self._log_buffer.append(logged_data_packet)
                    continue  # skip because we don't want to put the message in the queue
            else:
                if self._log_buffer:
                    # Log the buffer before logging the new message
                    self._log_the_buffer()

                self._log_counter = 0  # Reset the counter for other states

            # Put the message in the queue
            self._log_queue.put(logged_data_packet)

    def _log_the_buffer(self):
        """
        Adds the log buffer to the queue, so it can be logged to file.
        """
        for buffered_message in self._log_buffer:
            self._log_queue.put(buffered_message)
        self._log_buffer.clear()

    def truncate_decimal_place(self, obj_type: Any) -> str:
        """
        Truncates the decimal place of the object to 8 decimal places. Used by msgspec to
        convert numpy float64 to a string.
        :param obj_type: The object to truncate.
        :return: The truncated object.
        """
        return f"{obj_type:.8f}"

    def _prepare_log_dict(
        self,
        state: str,
        extension: str,
        imu_data_packets: deque[IMUDataPacket],
        processed_data_packets: deque[ProcessedDataPacket],
        predicted_apogee: float,
    ) -> deque[LoggedDataPacket]:
        """
        Creates a data packet dictionary representing a row of data to be logged.
        :param state: The current state of the airbrakes.
        :param extension: The current extension of the airbrakes.
        :param imu_data_packets: The IMU data packets to log.
        :param processed_data_packets: The processed data packets to log.
        :param: predicted_apogee: The predicted apogee of the rocket. Only logged with estimated
            data packets.
        :return: A deque of LoggedDataPacket objects.
        """
        logged_data_packets: deque[LoggedDataPacket] = deque()

        # Convert the imu data packets to a dictionary:
        for imu_data_packet in imu_data_packets:
            # Let's first add the state, extension field:
            logged_fields: LoggedDataPacket = {
                "state": state,
                "extension": extension,
            }
            # Convert the imu data packet to a dictionary
            # Using to_builtins() is much faster than asdict() for some reason
            imu_data_packet_dict: dict[str, int | float | list[str]] = to_builtins(imu_data_packet)
            logged_fields.update(imu_data_packet_dict)

            # Get the processed data packet fields:
            if isinstance(imu_data_packet, EstimatedDataPacket):
                processed_data_packet_dict: dict[str, float] = to_builtins(
                    processed_data_packets.popleft(), enc_hook=self.truncate_decimal_place
                )
                # Let's drop the "time_since_last_data_packet" field:
                processed_data_packet_dict.pop("time_since_last_data_packet", None)
                logged_fields.update(processed_data_packet_dict)

                # Add the predicted apogee field:
                logged_fields["predicted_apogee"] = predicted_apogee

            logged_data_packets.append(logged_fields)

        return logged_data_packets

    # ------------------------------- RUN IN A SEPARATE PROCESS -----------------------------------
    def _logging_loop(self) -> None:
        """
        The loop that saves data to the logs. It runs in parallel with the main loop.
        """
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal
        # Set up the csv logging in the new process
        with self.log_path.open(mode="a", newline="") as file_writer:
            writer = csv.DictWriter(file_writer, fieldnames=list(LoggedDataPacket.__annotations__))
            while True:
                # Get a message from the queue (this will block until a message is available)
                # Because there's no timeout, it will wait indefinitely until it gets a message.
                message_fields = self._log_queue.get()
                # If the message is the stop signal, break out of the loop
                if message_fields == STOP_SIGNAL:
                    break
                writer.writerow(self._truncate_floats(message_fields))

    def _truncate_floats(self, data: LoggedDataPacket) -> dict[str, str | object]:
        """
        Truncates the decimal place of the floats in the dictionary to 8 decimal places.
        :param data: The dictionary to truncate.
        :return: The truncated dictionary.
        """
        return {
            key: f"{value:.8f}" if isinstance(value, float) else value
            for key, value in data.items()
        }
