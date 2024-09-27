"""Module for logging data to a CSV file in real time."""

import collections
import csv
import multiprocessing
import signal
from pathlib import Path

from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from constants import LOG_BUFFER_SIZE, LOG_CAPACITY_AT_STANDBY, STOP_SIGNAL


class Logger:
    """
    A class that logs data to a CSV file. Similar to the IMU class, it runs in a separate process. This is because the
    logging process is I/O-bound, meaning that it spends most of its time waiting for the file to be written to. By
    running it in a separate process, we can continue to log data while the main loop is running.

    It uses the Python logging module to append the airbrake's current state, extension, and IMU data to our logs in
    real time.

    :param log_dir: The directory where the log files will be.
    """

    __slots__ = ("_log_buffer", "_log_counter", "_log_process", "_log_queue", "log_path")

    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)

        # Get all existing log files and find the highest suffix number
        existing_logs = list(log_dir.glob("log_*.csv"))
        max_suffix = max(int(log.stem.split("_")[-1]) for log in existing_logs) if existing_logs else 0

        # Buffer for StandbyState and LandedState
        self._log_counter = 0
        self._log_buffer = collections.deque(maxlen=LOG_BUFFER_SIZE)

        # Create a new log file with the next number in sequence
        self.log_path = log_dir / f"log_{max_suffix + 1}.csv"
        with self.log_path.open(mode="w", newline="") as file_writer:
            writer = csv.DictWriter(file_writer, fieldnames=LoggedDataPacket.__struct_fields__)
            writer.writeheader()

        # Makes a queue to store log messages, basically it's a process-safe list that you add to
        # the back and pop from front, meaning that things will be logged in the order they were
        # added.
        # Signals (like stop) are sent as strings, but data is sent as dictionaries
        self._log_queue: multiprocessing.Queue[dict[str, str] | str] = multiprocessing.Queue()

        # Start the logging process
        self._log_process = multiprocessing.Process(target=self._logging_loop, name="Logger")

    @property
    def is_running(self) -> bool:
        """
        Returns whether the logging process is running.
        """
        return self._log_process.is_alive()

    def start(self) -> None:
        """
        Starts the logging process. This is called before the main while loop starts.
        """
        self._log_process.start()

    def stop(self) -> None:
        """
        Stops the logging process. It will finish logging the current message and then stop.
        """
        self._log_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        # Waits for the process to finish before stopping it
        self._log_process.join()

    def log(self, logged_data_packets: collections.deque[LoggedDataPacket]) -> None:
        """
        Logs the current state, extension, and IMU data to the CSV file.
        :param logged_data_packets: the list of IMU data packets to log
        """
        # Loop through all the IMU data packets
        for logged_data_packet in logged_data_packets:
            # Formats the log message as a CSV line
            message_dict = {key: getattr(logged_data_packet, key) for key in logged_data_packet.__struct_fields__}

            if logged_data_packet.state in ["S", "L"]:  # S: StandbyState, L: LandedState
                if self._log_counter < LOG_CAPACITY_AT_STANDBY:
                    # add the count:
                    self._log_counter += 1
                else:
                    self._log_buffer.append(message_dict)
                    continue
            else:
                if self._log_buffer:
                    # Log the buffer before logging the new message
                    for buffered_message in self._log_buffer:
                        self._log_queue.put(buffered_message)
                    self._log_buffer.clear()

                self._log_counter = 0  # Reset the counter for other states

            # Put the message in the queue
            self._log_queue.put(message_dict)

    def _logging_loop(self) -> None:
        """
        The loop that saves data to the logs. It runs in parallel with the main loop.
        """
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal
        # Set up the csv logging in the new process
        with self.log_path.open(mode="a", newline="") as file_writer:
            writer = csv.DictWriter(file_writer, fieldnames=LoggedDataPacket.__struct_fields__)
            while True:
                # Get a message from the queue (this will block until a message is available)
                # Because there's no timeout, it will wait indefinitely until it gets a message.
                message_fields = self._log_queue.get()
                # If the message is the stop signal, break out of the loop
                if message_fields == STOP_SIGNAL:
                    break
                writer.writerow(message_fields)
