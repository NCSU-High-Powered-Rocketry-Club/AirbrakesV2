"""
Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket.
"""

import ast
import contextlib
import multiprocessing
import time
import typing
from pathlib import Path

import msgspec
import pandas as pd
from faster_fifo import Queue

from airbrakes.constants import (
    CHUNK_SIZE,
    DEFAULT,
    MAX_FETCHED_PACKETS,
    MAX_QUEUE_SIZE,
    STOP_SIGNAL,
)
from airbrakes.interfaces.base_imu import BaseIMU
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)

if typing.TYPE_CHECKING:
    from pandas.io.parsers.readers import TextFileReader


class MockIMU(BaseIMU):
    """
    A mock implementation of the IMU for testing purposes.

    It doesn't interact with any hardware and returns data read from a previous log file.
    """

    __slots__ = ("_headers", "_log_file_path", "_needed_fields", "file_metadata")

    def __init__(
        self,
        real_time_replay: bool,
        log_file_path: Path | None = None,
        start_after_log_buffer: bool = True,
    ):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a log
        file.

        We don't call the parent constructor as the IMU class has different     parameters, so we
        manually start the process that fetches data from the log file.
        :param real_time_replay: Whether to mimmick a real flight by sleeping for a set period, or
            run at full speed, e.g. for using it in the CI.
        :param log_file_path: The path of the log file to read data from.
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
            log_file_path = next(iter(Path(root_dir / "launch_data").glob("*.csv")))

        # If it's not a real time replay, we limit how big the queue gets when doing an integration
        # test, because we read the file much faster than update(), sometimes resulting thousands
        # of data packets in the queue, which will obviously mess up data processing calculations.
        # We limit it to 15 packets, which is more realistic for a real flight.
        msgpack_encoder = msgspec.msgpack.Encoder()
        msgpack_decoder = msgspec.msgpack.Decoder(type=EstimatedDataPacket | RawDataPacket | str)
        queued_imu_packets: Queue[IMUDataPacket] = Queue(
            maxsize=MAX_QUEUE_SIZE if real_time_replay else MAX_FETCHED_PACKETS,
            dumps=msgpack_encoder.encode,
            loads=msgpack_decoder.decode,
        )
        # Starts the process that fetches data from the log file
        data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop,
            args=(real_time_replay, start_after_log_buffer),
            name="Mock IMU Process",
        )

        self._log_file_path: Path = typing.cast("Path", log_file_path)

        self._headers: pd.DataFrame = self._read_csv(nrows=0, usecols=None)
        # Get the columns that are common between the data packet and the log file, since we only
        # care about those (it's also faster to read few columns rather than all)
        self._needed_fields = list(
            (set(EstimatedDataPacket.__struct_fields__) | set(RawDataPacket.__struct_fields__))
            & set(self._headers.columns)
        )
        file_metadata: dict = MockIMU.read_file_metadata()
        self.file_metadata = file_metadata.get(self._log_file_path.name, {})

        super().__init__(data_fetch_process, queued_imu_packets)

    @staticmethod
    def read_file_metadata() -> dict:
        """
        Reads the metadata from the log file and returns it as a dictionary.
        """
        metadata = Path("launch_data/metadata.json")
        return msgspec.json.decode(metadata.read_text())

    @staticmethod
    def _convert_invalid_fields(value) -> list | None:
        """
        Convert invalid fields to Python objects or None.

        :param value: The value to convert.
        :return: The converted value.
        """
        return None if not value else ast.literal_eval(value)  # Convert string to list

    def _read_csv(
        self,
        *,
        start_index: int = 0,
        usecols: list[str] | object = DEFAULT,
        **kwargs,
    ) -> "pd.DataFrame | TextFileReader":
        """
        Reads the csv file and returns it as a pandas DataFrame.

        :param start_index: The index to start reading the file from. Must be a keyword argument.
        :param usecols: The columns to read from the file. Must be a keyword argument.
        :param kwargs: Additional keyword arguments to pass to pd.read_csv.
        :return: The DataFrame or TextFileReader object.
        """
        # Read the csv, starting from the row after the log buffer, and using only the valid columns
        return pd.read_csv(
            self._log_file_path,
            engine="c",
            usecols=self._needed_fields if usecols is DEFAULT else usecols,
            converters={"invalid_fields": MockIMU._convert_invalid_fields},
            skiprows=range(1, start_index + 1),
            memory_map=True,
            **kwargs,
        )

    def _calculate_start_index(self) -> int:
        """
        Calculate the start index based on log buffer size and time differences.

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

    def _read_file(self, real_time_replay: bool, start_after_log_buffer: bool = False) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.

        :param real_time_replay: Whether to mimic a real flight by sleeping for a set period, or run
            at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        start_index = self._calculate_start_index() if start_after_log_buffer else 0

        launch_raw_data_packet_rate = 1 / self.file_metadata["imu_details"]["raw_packet_frequency"]

        # and chunk read the file because it's faster and memory efficient
        reader: TextFileReader = typing.cast(
            "TextFileReader",
            self._read_csv(
                start_index=start_index,
                chunksize=CHUNK_SIZE,
            ),
        )
        # Iterate over the rows of the dataframe and put the data packets in the queue
        for chunk in reader:
            for row in chunk.itertuples(index=False):
                start_time = time.time()
                # Convert the named tuple to a dictionary and remove any NaN values:
                row_dict = {k: v for k, v in row._asdict().items() if pd.notna(v)}

                # Check if the process should stop:
                if not self.is_running:
                    break

                # If the row has the scaledAccelX field, it is a raw data packet, otherwise it is
                # an estimated data packet
                if row_dict.get("scaledAccelX"):
                    imu_data_packet = RawDataPacket(**row_dict)
                elif row_dict.get("estPressureAlt"):
                    imu_data_packet = EstimatedDataPacket(**row_dict)
                else:
                    continue

                # Put the packet in the queue
                self._queued_imu_packets.put(imu_data_packet)

                # Sleep only if we are running a real-time replay
                # Our IMU sends raw data at 500 Hz (or in older files 1000hz), so we sleep for 1 ms
                # between each packet to pretend to be real-time
                if real_time_replay and type(imu_data_packet) is RawDataPacket:
                    # Mimic the polling interval so it "runs in real time"
                    end_time = time.time()
                    time.sleep(max(0.0, launch_raw_data_packet_rate - (end_time - start_time)))

    def _fetch_data_loop(
        self, real_time_replay: bool, start_after_log_buffer: bool = False
    ) -> None:
        """
        A wrapper function to suppress KeyboardInterrupt exceptions when reading the log file.

        :param real_time_replay: Whether to mimic a real flight by sleeping for a set period, or run
            at full speed.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        # Unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            self._read_file(real_time_replay, start_after_log_buffer)

        # For the mock, once we're done reading the file, we say it is no longer running
        self._running.value = False
        self._queued_imu_packets.put(STOP_SIGNAL)
