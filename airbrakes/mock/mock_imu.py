"""Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket."""

import ast
import contextlib
import multiprocessing
import time
from pathlib import Path

import pandas as pd

from airbrakes.data_handling.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from airbrakes.hardware.imu import IMU
from constants import LOG_BUFFER_SIZE, MAX_QUEUE_SIZE, SIMULATION_MAX_QUEUE_SIZE


class MockIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns data read from a previous log file.
    """

    __slots__ = ("_log_file_path",)

    def __init__(
        self,
        log_file_path: Path | bool,
        real_time_simulation: bool,
        start_after_log_buffer: bool = False,
    ):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a
        log file.
        :param log_file_path: The path of the log file to read data from.
        :param real_time_simulation: Whether to simulate a real flight by sleeping for a set
        period, or run at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        self._log_file_path = log_file_path
        # Check if the launch data file exists:
        if not log_file_path:
            # Just use the first file in the `launch_data` directory:
            self._log_file_path = next(iter(Path("launch_data").glob("*.csv")))

        # We don't call the parent constructor as the IMU class has different parameters, so we
        # manually start the process that fetches data from the log file

        # If it's not a real time sim, we limit how big the queue gets when doing an integration
        # test, because we read the file much faster than update(), sometimes resulting thousands
        # of data packets in the queue, which will obviously mess up data processing calculations.
        # We limit it to 15 packets, which is more realistic for a real flight.
        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue(
            MAX_QUEUE_SIZE if real_time_simulation else SIMULATION_MAX_QUEUE_SIZE
        )

        # Starts the process that fetches data from the log file
        self._data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop,
            args=(
                self._log_file_path,
                real_time_simulation,
                start_after_log_buffer,
            ),
            name="Mock IMU Process",
        )

        # Makes a boolean value that is shared between processes
        self._running = multiprocessing.Value("b", False)

    @staticmethod
    def _convert_invalid_fields(value):
        if not value:
            return None
        return ast.literal_eval(value)  # Convert string to list

    def _read_file(
        self, log_file_path: Path, real_time_simulation: bool, start_after_log_buffer: bool = False
    ) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.
        :param log_file_path: the name of the log file to read data from located in scripts/imu_data
        :param real_time_simulation: Whether to simulate a real flight by sleeping for a set period,
        or run at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        start_index = 0
        if start_after_log_buffer:
            # We need to loop through the file and calculate the time difference to find the index
            # at which the log buffer starts. That index will be used as the start point.
            # Read the CSV file in chunks to avoid loading the entire file into memory
            chunk_size = LOG_BUFFER_SIZE + 1  # The chunk size is close to our log buffer size.
            for chunk in pd.read_csv(
                log_file_path,
                chunksize=chunk_size,
                converters={"invalid_fields": self._convert_invalid_fields},
            ):
                # Calculate the time difference between consecutive rows
                chunk["time_diff"] = chunk["timestamp"].diff()
                # Find the index where the time difference exceeds 1 second
                buffer_end_index = chunk[chunk["time_diff"] > 1e9].index
                if not buffer_end_index.empty:
                    start_index = buffer_end_index[0]
                    break

        # Using pandas and itertuples to read the file:
        df_header = pd.read_csv(log_file_path, nrows=0)
        # Get the columns that are common between the data packet and the log file, since we only
        # care about those
        valid_columns = list(
            (set(EstimatedDataPacket.__struct_fields__) | set(RawDataPacket.__struct_fields__))
            & set(df_header.columns)
        )

        # Read the csv, starting from the row after the log buffer, and using only the valid columns
        df = pd.read_csv(
            log_file_path,
            skiprows=range(1, start_index + 1),
            engine="c",
            usecols=valid_columns,
            converters={"invalid_fields": self._convert_invalid_fields},
        )
        for row in df.itertuples(index=False):
            start_time = time.time()
            # Convert the named tuple to a dictionary and remove any NaN values:
            row_dict = {k: v for k, v in row._asdict().items() if pd.notna(v)}

            # Check if the process should stop:
            if not self._running.value:
                break

            if row_dict.get("scaledAccelX"):  # RawDataPacket
                imu_data_packet = RawDataPacket(**row_dict)
            else:
                imu_data_packet = EstimatedDataPacket(**row_dict)

            # Put the packet in the queue
            self._data_queue.put(imu_data_packet)

            # sleep only if we are running a real-time simulation
            # Our IMU sends raw data at 1000 Hz, so we sleep for 1 ms between each packet to
            # pretend to be real-time
            if real_time_simulation and isinstance(imu_data_packet, RawDataPacket):
                # Simulate polling interval
                end_time = time.time()
                time.sleep(max(0.0, 0.001 - (end_time - start_time)))

    def _fetch_data_loop(
        self, log_file_path: Path, real_time_simulation: bool, start_after_log_buffer: bool = False
    ) -> None:
        """A wrapper function to suppress KeyboardInterrupt exceptions when reading the log file."""
        # unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            self._read_file(log_file_path, real_time_simulation, start_after_log_buffer)

        # For the mock, once we're done reading the file, we say it is no longer running
        self._running.value = False
