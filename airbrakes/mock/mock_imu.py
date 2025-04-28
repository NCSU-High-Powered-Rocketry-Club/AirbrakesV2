"""Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket."""

import contextlib
import multiprocessing
import time
import typing
from pathlib import Path

import msgspec
import polars as pl
from faster_fifo import Queue

from airbrakes.constants import (
    BUFFER_SIZE_IN_BYTES,
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


class MockIMU(BaseIMU):
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
        real_time_replay: bool,
        log_file_path: Path | None = None,
        start_after_log_buffer: bool = True,
    ):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a
            log file. We don't call the parent constructor as the IMU class has different
            parameters, so we manually start the process that fetches data from the log file.
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
        queued_imu_packets: Queue[IMUDataPacket] = Queue(
            maxsize=MAX_QUEUE_SIZE if real_time_replay else MAX_FETCHED_PACKETS * 10,
            max_size_bytes=BUFFER_SIZE_IN_BYTES,
        )
        # Starts the process that fetches data from the log file
        context = multiprocessing.get_context("forkserver")
        data_fetch_process = context.Process(
            target=self._fetch_data_loop,
            args=(real_time_replay, start_after_log_buffer),
            name="Mock IMU Process",
        )

        self._log_file_path: Path = typing.cast("Path", log_file_path)
        self._headers: list[str] | None = None  # The headers of the csv file being read.
        self._needed_fields: list[str] | None = None  # The fields we need to read from the csv

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

    def _read_csv(
        self,
        *,
        start_index: int = 0,
        usecols: list[str] | object = DEFAULT,
        **kwargs,
    ) -> pl.DataFrame:
        """Reads the csv file and returns it as a polars DataFrame.

        :param start_index: The index to start reading the file from. Must be a keyword argument.
        :param usecols: The columns to read from the file. Must be a keyword argument.
        :param kwargs: Additional keyword arguments to pass to pl.read_csv.

        :return: The DataFrame or TextFileReader object.
        """
        # This is here because of issues with using "fork" multiprocessing on Linux with polars.
        # We should be using "spawn", and that will be the default in Python 3.14.
        self._headers: list[str] = pl.scan_csv(self._log_file_path).collect_schema().names()
        # Get the columns that are common between the data packet and the log file, since we only
        # care about those (it's also faster to read few columns rather than all). This needs to
        # be in the same order as the source definition:
        # Get all field names from both packet types
        raw_fields = list(RawDataPacket.__struct_fields__)
        estimated_fields = list(EstimatedDataPacket.__struct_fields__)

        # Combine fields in the desired order (raw first, then estimated)
        all_fields_ordered = raw_fields + [f for f in estimated_fields if f not in raw_fields]

        # Filter to only include fields that exist in the CSV headers
        self._needed_fields = [field for field in all_fields_ordered if field in self._headers]

        # Read the csv, starting from the row after the log buffer, and using only the valid columns
        return pl.read_csv(
            self._log_file_path,
            columns=self._needed_fields if usecols is DEFAULT else usecols,
            skip_rows_after_header=start_index,
            infer_schema_length=10,
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

        result = (
            pl.scan_csv(self._log_file_path)
            .with_row_index("index")  # Add an index column to the DataFrame
            .with_columns(pl.col("timestamp").diff().alias("time_diff"))  # Calculate time diff
            .filter(pl.col("time_diff") > 1e9)  # Filter rows with time diff > 1 second
            .select("index")  # Select the index of the first row with time diff > 1 second
            .collect()
        )
        return result["index"][0] if not result.is_empty() else 0  # Default to 0 if no index found

    def _read_file(self, real_time_replay: bool, start_after_log_buffer: bool = False) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.
        :param real_time_replay: Whether to mimic a real flight by sleeping for a set period,
        or run at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        start_index = self._calculate_start_index() if start_after_log_buffer else 0

        launch_raw_data_packet_rate = 1 / self.file_metadata["imu_details"]["raw_packet_frequency"]

        reader: pl.DataFrame = self._read_csv(start_index=start_index)

        # Iterate over the rows of the dataframe and put the data packets in the queue
        packets = []
        for row in reader.iter_rows(named=True):
            start_time = time.perf_counter()
            row_dict = {k: v for k, v in row.items() if v is not None}

            # If the row has the scaledAccelX field, it is a raw data packet, otherwise it is
            # an estimated data packet
            if row_dict.get("scaledAccelX"):
                imu_data_packet = RawDataPacket(**row_dict)
            elif row_dict.get("estPressureAlt"):  # checking for estPressureAlt
                imu_data_packet = EstimatedDataPacket(**row_dict)
            else:
                continue

            # Put the packet in the queue in a batch, to reduce the cost of acquiring locks.
            # TODO: While faster under -f, this method has a drawback of artifically increasing the
            # convergence time, and negatively affecting the "real-time" experience when not running
            # under -f. A way to fix this would be to add another code path if running under -f.
            if len(packets) < MAX_FETCHED_PACKETS:
                packets.append(imu_data_packet)
            else:
                self._queued_imu_packets.put_many(packets)
                packets = []

            # Sleep only if we are running a real-time replay
            # Our IMU sends raw data at 500 Hz (or in older files 1000hz), so we sleep for 1 or 2 ms
            # between each packet to pretend to be real-time
            if real_time_replay and type(imu_data_packet) is RawDataPacket:
                # Mimic the polling interval so it "runs in real time"
                end_time = time.perf_counter()
                time.sleep(max(0.0, launch_raw_data_packet_rate - (end_time - start_time)))

        # Put the remaining packets in the queue
        if packets:
            self._queued_imu_packets.put_many(packets)

    def _fetch_data_loop(
        self,
        real_time_replay: bool,
        start_after_log_buffer: bool = False,
    ) -> None:
        """
        A wrapper function to suppress KeyboardInterrupt exceptions when reading the log file.
        :param real_time_replay: Whether to mimic a real flight by sleeping for a set period,
        or run at full speed.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
        was filled for Standby state.
        """
        self._setup_queue_serialization_method()
        # Unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            self._read_file(real_time_replay, start_after_log_buffer)

        # For the mock, once we're done reading the file, we say it is no longer running
        self._running.value = False
        # If we don't put the STOP_SIGNAL in the queue, the main process will wait till IMU_TIMEOUT
        # seconds before exiting, which is not what we want.
        self._queued_imu_packets.put(STOP_SIGNAL)
