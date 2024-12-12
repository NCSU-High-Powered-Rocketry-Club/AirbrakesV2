"""Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket."""

import ast
import contextlib
import multiprocessing
import time
import typing
from pathlib import Path

import msgspec
import pandas as pd
from pandas.io.parsers.readers import TextFileReader

from airbrakes.data_handling.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from airbrakes.hardware.imu import IMU
from constants import (
    LOG_BUFFER_SIZE,
    MAX_QUEUE_SIZE,
    RAW_DATA_PACKET_SAMPLING_RATE,
    SIMULATION_MAX_QUEUE_SIZE,
)
from utils import convert_to_nanoseconds

CHUNK_SIZE = LOG_BUFFER_SIZE + 1
"""The size of the chunk to read from the log file at a time. This has 2 benefits. Less memory
usage and faster initial read of the file."""

DEFAULT = object()
"""Default sentinel value for usecols in the read_csv method."""


class MockIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns data read from a previous log file.
    """

    __slots__ = (
        "_headers",
        "_log_file_path",
        "_needed_fields",
        "file_metadata",
    )

    def __init__(
        self,
        real_time_simulation: bool,
        log_file_path: Path | None = None,
        start_after_log_buffer: bool = True,
    ):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a
        log file.

        We don't call the parent constructor as the IMU class has different parameters, so we
        manually start the process that fetches data from the log file
        :param log_file_path: The path of the log file to read data from.
        :param real_time_simulation: Whether to simulate a real flight by sleeping for a set
        period, or run at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        # Check if the launch data file exists:
        if log_file_path is None:
            # Just use the first file in the `launch_data` directory:
            self._log_file_path = next(iter(Path("launch_data").glob("*.csv")))
        self._log_file_path: Path = typing.cast(Path, log_file_path)

        self._headers: pd.DataFrame = self._read_csv(nrows=0, usecols=None)
        self._needed_fields = list(
            (set(EstimatedDataPacket.__struct_fields__) | set(RawDataPacket.__struct_fields__))
            & set(self._headers.columns)
        )

        self.file_metadata: dict = self.read_file_metadata()
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
                real_time_simulation,
                start_after_log_buffer,
            ),
            name="Mock IMU Process",
        )

        # Makes a boolean value that is shared between processes
        self._running = multiprocessing.Value("b", False)

    def _read_csv(
        self,
        *,
        start_index: int = 0,
        usecols: list[str] | typing.Literal[DEFAULT] = DEFAULT,
        **kwargs,
    ) -> "pd.DataFrame | TextFileReader":
        """Reads the csv file and returns it as a pandas DataFrame."""
        return pd.read_csv(
            self._log_file_path,
            engine="c",
            usecols=self._needed_fields if usecols is DEFAULT else usecols,
            converters={"invalid_fields": MockIMU._convert_invalid_fields},
            skiprows=range(1, start_index + 1),
            **kwargs,
        )

    def read_file_metadata(self) -> dict:
        """
        Reads the metadata from the log file and returns it as a dictionary.
        """
        metadata = Path("launch_data/metadata.json")
        decoded_metadata = msgspec.json.decode(metadata.read_text())

        if self._log_file_path.name not in decoded_metadata:
            return {}

        return decoded_metadata[self._log_file_path.name]

    @staticmethod
    def _convert_invalid_fields(value) -> list:
        """
        Convert invalid fields to Python objects or None.
        :param value: The value to convert.
        :return: The converted value
        """
        return None if not value else ast.literal_eval(value)  # Convert string to list

    def _calculate_start_index(self) -> int:
        """
        Calculate the start index based on log buffer size and time differences.
        :param log_file_path: The path of the log file to read data from.
        :return: The index where the log buffer ends.
        """
        metadata_buffer_index: int | None = self.file_metadata["flight_data"]["log_buffer_index"]

        if metadata_buffer_index:
            return metadata_buffer_index

        # We read the file in small chunks because it is faster than reading the whole file at once
        for chunk in self._read_csv(
            chunksize=CHUNK_SIZE,
            usecols=["timestamp"],
        ):
            chunk["time_diff"] = chunk["timestamp"].diff()
            buffer_end_index = chunk[chunk["time_diff"] > 1e9].index
            if not buffer_end_index.empty:
                return buffer_end_index[0]
        return 0

    def _read_file(self, real_time_simulation: bool, start_after_log_buffer: bool = False) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.
        :param real_time_simulation: Whether to simulate a real flight by sleeping for a set period,
        or run at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        start_index = self._calculate_start_index() if start_after_log_buffer else 0

        # Get the columns that are common between the data packet and the log file, since we only
        # care about those
        # Read the csv, starting from the row after the log buffer, and using only the valid columns
        # and chunk read the file because it's faster and memory efficient
        reader: TextFileReader = typing.cast(
            TextFileReader,
            self._read_csv(
                start_index=start_index,
                chunksize=CHUNK_SIZE,
            ),
        )
        # Using pandas and itertuples to read the file:
        for chunk in reader:
            for row in chunk.itertuples(index=False):
                start_time = time.time()
                # Convert the named tuple to a dictionary and remove any NaN values:
                row_dict = {k: v for k, v in row._asdict().items() if pd.notna(v)}

                # Check if the process should stop:
                if not self._running.value:
                    break

                # If the row has the scaledAccelX field, it is a raw data packet, otherwise it is an
                # estimated data packet
                if row_dict.get("scaledAccelX"):
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
                    time.sleep(max(0.0, RAW_DATA_PACKET_SAMPLING_RATE - (end_time - start_time)))

    def _fetch_data_loop(
        self, real_time_simulation: bool, start_after_log_buffer: bool = False
    ) -> None:
        """
        A wrapper function to suppress KeyboardInterrupt exceptions when reading the log file.
        :param real_time_simulation: Whether to simulate a real flight by sleeping for a set period,
        or run at full speed.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        # Unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            self._read_file(real_time_simulation, start_after_log_buffer)
            # For the mock, once we're done reading the file, we say it is no longer running
            self._running.value = False

    def get_launch_time(self) -> int:
        """Gets the launch time, from reading the csv file.

        :return int: The corresponding launch time in nanoseconds. Returns 0 if the launch time
            could not be found.
        """

        # Read the file, and check when the "state" field shows "M", or when the magnitude of the
        # estimated linear acceleration is greater than 3 m/s^2:
        if "state" in self._headers.columns:
            df = self._read_csv(usecols=["timestamp", "state"])
            # Check for the "M" state
            launch_time = df.loc[df["state"] == "M", "timestamp"]
            if not launch_time.empty:
                return convert_to_nanoseconds(launch_time.iloc[0])
            return 0

        df = self._read_csv(
            usecols=[
                "timestamp",
                "estLinearAccelX",
                "estLinearAccelY",
                "estLinearAccelZ",
            ]
        )

        # Calculate the magnitude of the estimated linear acceleration
        df["estLinearAccelMag"] = (
            df["estLinearAccelX"].astype(float) ** 2
            + df["estLinearAccelY"].astype(float) ** 2
            + df["estLinearAccelZ"].astype(float) ** 2
        ) ** 0.5

        # Check for the magnitude condition
        launch_time = df.loc[df["estLinearAccelMag"] > 3, "timestamp"]
        if not launch_time.empty:
            return convert_to_nanoseconds(launch_time.iloc[0])
        return 0
