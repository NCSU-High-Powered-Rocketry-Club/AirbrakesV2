"""Module for logging data to a CSV file in real time."""

import collections
import csv
import multiprocessing
import signal
from pathlib import Path

from airbrakes.constants import CSV_HEADERS, STOP_SIGNAL
from airbrakes.imu.imu_data_packet import IMUDataPacket


class Logger:
    """
    A class that logs data to a CSV file. Similar to the IMU class, it runs in a separate process. This is because the
    logging process is I/O-bound, meaning that it spends most of its time waiting for the file to be written to. By
    running it in a separate process, we can continue to log data while the main loop is running.

    It uses the Python logging module to append the airbrake's current state, extension, and IMU data to our logs in
    real time.

    :param log_dir: The directory where the log files will be.
    """

    __slots__ = ("_log_process", "_log_queue", "log_path")

    def __init__(self, log_dir: Path):
        log_dir.mkdir(parents=True, exist_ok=True)

        # Get all existing log files and find the highest suffix number
        existing_logs = list(log_dir.glob("log_*.csv"))
        max_suffix = max(int(log.stem.split("_")[-1]) for log in existing_logs) if existing_logs else 0

        # Create a new log file with the next number in sequence
        self.log_path = log_dir / f"log_{max_suffix + 1}.csv"
        with self.log_path.open(mode="w", newline="") as file_writer:
            writer = csv.DictWriter(file_writer, fieldnames=CSV_HEADERS)
            writer.writeheader()

        # Makes a queue to store log messages, basically it's a process-safe list that you add to
        # the back and pop from front, meaning that things will be logged in the order they were
        # added.
        # Signals (like stop) are sent as strings, but data is sent as dictionaries
        self._log_queue: multiprocessing.Queue[dict[str, str] | str] = multiprocessing.Queue()

        # Start the logging process
        self._log_process = multiprocessing.Process(target=self._logging_loop, name="Logger")

    def __enter__(self):
        """This is what is run when the context manager is entered, i.e. a `with` statement."""
        self.start()
        return self

    def __exit__(self, _, exc_val: object, __):
        """This is what is run when the context manager is exited, i.e. when the `with` block ends."""
        # If a KeyboardInterrupt was raised, we want to stop the logger cleanly, and not raise
        # the exception again
        self.stop()
        return isinstance(exc_val, KeyboardInterrupt)  # Suppress propogation only for Ctrl+C

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

    def log(self, state: str, extension: float, imu_data_list: collections.deque[IMUDataPacket]) -> None:
        """
        Logs the current state, extension, and IMU data to the CSV file.
        :param state: the current state of the airbrakes state machine
        :param extension: the current extension of the airbrakes
        :param imu_data_list: the current list of IMU data packets to log
        """
        # Loop through all the IMU data packets
        for imu_data in imu_data_list:
            # Formats the log message as a CSV line
            message_dict = {"state": state, "extension": extension}
            message_dict.update({key: getattr(imu_data, key) for key in imu_data.__struct_fields__})
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
            writer = csv.DictWriter(file_writer, fieldnames=CSV_HEADERS)
            while True:
                # Get a message from the queue (this will block until a message is available)
                # Because there's no timeout, it will wait indefinitely until it gets a message.
                message_fields = self._log_queue.get()
                # If the message is the stop signal, break out of the loop
                if message_fields == STOP_SIGNAL:
                    break
                writer.writerow(message_fields)
