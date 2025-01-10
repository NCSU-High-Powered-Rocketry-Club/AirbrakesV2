"""Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket."""

import ast
import contextlib
import multiprocessing
import sys
import time
from pathlib import Path

import pandas as pd

if sys.platform != "win32":
    from faster_fifo import Queue
else:
    from functools import partial

    from airbrakes.utils import get_all_from_queue

from airbrakes.constants import (
    LOG_BUFFER_SIZE,
    MAX_FETCHED_PACKETS,
    MAX_QUEUE_SIZE,
    RAW_DATA_PACKET_SAMPLING_RATE,
    STOP_SIGNAL,
)
from airbrakes.data_handling.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from airbrakes.hardware.base_imu import BaseIMU


class MockIMU(BaseIMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns data read from a previous log file.
    """

    __slots__ = ("_log_file_path",)

    def __init__(
        self,
        real_time_replay: bool,
        log_file_path: Path | None = None,
        start_after_log_buffer: bool = True,
    ):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a
        log file.

        We don't call the parent constructor as the IMU class has different parameters, so we
        manually start the process that fetches data from the log file
        :param log_file_path: The path of the log file to read data from.
        :param real_time_replay: Whether to mimmick a real flight by sleeping for a set
        period, or run at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        self._log_file_path = log_file_path
        # Check if the launch data file exists:
        if log_file_path is None:
            # Just use the first file in the `launch_data` directory:
            # Note: We do this convoluted way because we want to make it work with the one liner
            # `uvx --from git+... mock` on any machine from any state.
            root_dir = Path(__file__).parent.parent.parent
            self._log_file_path = next(iter(Path(root_dir / "launch_data").glob("*.csv")))

        # If it's not a real time replay, we limit how big the queue gets when doing an integration
        # test, because we read the file much faster than update(), sometimes resulting thousands
        # of data packets in the queue, which will obviously mess up data processing calculations.
        # We limit it to 15 packets, which is more realistic for a real flight.
        if sys.platform == "win32":
            # On Windows, we use a multiprocessing.Queue because the faster_fifo.Queue is not
            # available on Windows
            data_queue = multiprocessing.Queue(
                maxsize=MAX_QUEUE_SIZE if real_time_replay else MAX_FETCHED_PACKETS
            )

            data_queue.get_many = partial(get_all_from_queue, data_queue)
        else:
            data_queue: Queue[IMUDataPacket] = Queue(
                maxsize=MAX_QUEUE_SIZE if real_time_replay else MAX_FETCHED_PACKETS
            )
        # Starts the process that fetches data from the log file
        data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop,
            args=(self._log_file_path, real_time_replay, start_after_log_buffer),
            name="Mock IMU Process",
        )

        super().__init__(data_fetch_process, data_queue)

    @staticmethod
    def _convert_invalid_fields(value) -> list:
        """
        Convert invalid fields to Python objects or None.
        :param value: The value to convert.
        :return: The converted value
        """
        return None if not value else ast.literal_eval(value)  # Convert string to list

    @staticmethod
    def _calculate_start_index(log_file_path: Path) -> int:
        """
        Calculate the start index based on log buffer size and time differences.
        :param log_file_path: The path of the log file to read data from.
        :return: The index where the log buffer ends.
        """
        # We read the file in small chunks because it is faster than reading the whole file at once
        chunk_size = LOG_BUFFER_SIZE + 1
        for chunk in pd.read_csv(
            log_file_path,
            chunksize=chunk_size,
            converters={"invalid_fields": MockIMU._convert_invalid_fields},
        ):
            chunk["time_diff"] = chunk["timestamp"].diff()
            buffer_end_index = chunk[chunk["time_diff"] > 1e9].index
            if not buffer_end_index.empty:
                return buffer_end_index[0]
        return 0

    def _read_file(
        self, log_file_path: Path, real_time_replay: bool, start_after_log_buffer: bool = False
    ) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.
        :param log_file_path: the name of the log file to read data from located in scripts/imu_data
        :param real_time_replay: Whether to mimmick a real flight by sleeping for a set period,
        or run at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        start_index = self._calculate_start_index(log_file_path) if start_after_log_buffer else 0

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
            skiprows=list(range(1, start_index + 1)),
            engine="c",
            usecols=valid_columns,
            converters={"invalid_fields": MockIMU._convert_invalid_fields},
        )

        # Iterate over the rows of the dataframe and put the data packets in the queue
        for row in df.itertuples(index=False):
            start_time = time.time()
            # Convert the named tuple to a dictionary and remove any NaN values:
            row_dict = {k: v for k, v in row._asdict().items() if pd.notna(v)}

            # Check if the process should stop:
            if not self.is_running:
                break

            # If the row has the scaledAccelX field, it is a raw data packet, otherwise it is an
            # estimated data packet
            if row_dict.get("scaledAccelX"):
                imu_data_packet = RawDataPacket(**row_dict)
            else:
                imu_data_packet = EstimatedDataPacket(**row_dict)

            # Put the packet in the queue
            self._data_queue.put(imu_data_packet)

            # sleep only if we are running a real-time replay
            # Our IMU sends raw data at 1000 Hz, so we sleep for 1 ms between each packet to
            # pretend to be real-time
            if real_time_replay and isinstance(imu_data_packet, RawDataPacket):
                # Mimmick polling interval
                end_time = time.time()
                time.sleep(max(0.0, RAW_DATA_PACKET_SAMPLING_RATE - (end_time - start_time)))

    def _fetch_data_loop(
        self, log_file_path: Path, real_time_replay: bool, start_after_log_buffer: bool = False
    ) -> None:
        """
        A wrapper function to suppress KeyboardInterrupt exceptions when reading the log file.
        :param log_file_path: the name of the log file to read data from located in scripts/imu_data
        :param real_time_replay: Whether to mimmick a real flight by sleeping for a set period,
        or run at full speed.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        # Unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            self._read_file(log_file_path, real_time_replay, start_after_log_buffer)

        # For the mock, once we're done reading the file, we say it is no longer running
        self._running.value = False
        self._data_queue.put(STOP_SIGNAL)
