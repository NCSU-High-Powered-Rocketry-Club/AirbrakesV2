"""
Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket.
"""

import contextlib
import queue
import threading
import time
import typing
from pathlib import Path

import msgspec
import msgspec.json
import polars as pl

import airbrakes.constants
from airbrakes.constants import BUSY_WAIT_SECONDS, REALTIME_PLAYBACK_SPEED, STOP_SIGNAL
from airbrakes.interfaces.base_imu import BaseIMU
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from airbrakes.utils import convert_to_nanoseconds


class RocketParameters(msgspec.Struct):
    """
    Rocket parameters needed for IMU processing.
    """

    rocket_Cd: float | None
    rocket_mass_kg: float | None
    rocket_cross_sectional_area_m2: float | None


class MockIMU(BaseIMU):
    """
    A mock implementation of the IMU for testing purposes.

    It doesn't interact with any hardware and returns data read from a previous log file.
    """

    __slots__ = (
        "_headers",
        "_log_file_path",
        "_needed_fields",
        "_sim_speed_factor",
        "file_metadata",
        "rocket_parameters",
    )

    def __init__(
        self,
        real_time_replay: float = REALTIME_PLAYBACK_SPEED,
        log_file_path: Path | None = None,
        start_after_log_buffer: bool = True,
    ):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a log
        file.

        We don't call the parent constructor as the IMU class has different parameters, so we
        manually start the thread that fetches data from the log file.
        :param real_time_replay: Whether to mimmick a real flight by sleeping for a set period, or
            run at full speed, e.g. for using it in the CI.
        :param log_file_path: The path of the log file to read data from.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        # Check if the launch data file exists:
        if log_file_path is None:
            # Just use the first file in the `launch_data` directory:
            # Note: We do this convoluted way because we want to make it work with the one liner
            # `uvx --from git+... mock` on any machine from any state.
            root_dir = Path(__file__).parent.parent.parent
            log_file_path = next(iter(Path(root_dir / "launch_data").glob("*.csv")))

        self._log_file_path: Path = typing.cast("Path", log_file_path)

        if self._log_file_path == Path("launch_data/legacy_launch_2.csv"):
            raise ValueError("There is no data for this flight, please choose another file.")

        queued_imu_packets: queue.SimpleQueue[IMUDataPacket] = queue.SimpleQueue()
        # Starts the thread that fetches data from the log file
        data_fetch_thread = threading.Thread(
            target=self._fetch_data_loop,
            args=(start_after_log_buffer,),
            name="Mock IMU Thread",
            daemon=True,
        )

        self._sim_speed_factor = real_time_replay

        file_metadata: dict = MockIMU.read_all_metadata()
        self.file_metadata = file_metadata.get(self._log_file_path.name, {})
        self.rocket_parameters: RocketParameters = self._get_rocket_parameters(self.file_metadata)

        if self.rocket_parameters.rocket_mass_kg is not None:
            airbrakes.constants.ROCKET_DRY_MASS_KG = self.rocket_parameters.rocket_mass_kg
        if self.rocket_parameters.rocket_Cd is not None:
            airbrakes.constants.ROCKET_CD = self.rocket_parameters.rocket_Cd
        if self.rocket_parameters.rocket_cross_sectional_area_m2 is not None:
            airbrakes.constants.ROCKET_CROSS_SECTIONAL_AREA_M2 = (
                self.rocket_parameters.rocket_cross_sectional_area_m2
            )

        super().__init__(data_fetch_thread, queued_imu_packets)

    @staticmethod
    def read_all_metadata() -> dict:
        """
        Reads the metadata from the log file and returns it as a dictionary.
        """
        metadata = Path("launch_data/metadata.json")
        return msgspec.json.decode(metadata.read_text())

    def _get_rocket_parameters(self, metadata: dict) -> RocketParameters:
        """
        Extracts the rocket parameters from the metadata dictionary.

        :param metadata: The metadata dictionary.
        :return: The RocketParameters object.
        """
        rocket_data = metadata.get("rocket", {})
        return RocketParameters(
            rocket_Cd=rocket_data.get("rocket_Cd"),
            rocket_mass_kg=rocket_data.get("rocket_mass_kg"),
            rocket_cross_sectional_area_m2=rocket_data.get("rocket_cross_sectional_area_m2"),
        )

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE THREAD -------------------------

    def _scan_csv(
        self,
        *,
        start_index: int = 0,
        **kwargs,
    ) -> pl.LazyFrame:
        """
        Reads the csv file and returns it as a polars LazyFrame.

        :param start_index: The index to start reading the file from. Must be a keyword argument.
        :param kwargs: Additional keyword arguments to pass to pl.read_csv.
        :return: The DataFrame or TextFileReader object.
        """
        self._headers: list[str] = pl.scan_csv(self._log_file_path).collect_schema().names()
        # Get the columns that are common between the data packet and the log file, since we only
        # care about those (it's also faster to read few columns rather than all). This needs to
        # be in the same order as the source definition:
        # Get all field names from both packet types
        raw_fields = list(RawDataPacket.__struct_fields__)
        estimated_fields = list(EstimatedDataPacket.__struct_fields__)

        # Combine fields in the desired order (raw first, then estimated)
        all_fields_ordered = raw_fields + [f for f in estimated_fields if f not in raw_fields]

        # The fields we need to read from the csv:
        self._needed_fields = [field for field in all_fields_ordered if field in self._headers]

        # Read the csv, starting from the row after the log buffer, and using only the valid columns
        return pl.scan_csv(
            self._log_file_path,
            has_header=True,
            skip_rows_after_header=start_index,
            infer_schema_length=10,
            **kwargs,
        ).select(self._needed_fields)

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE PROCESS -------------------------
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

    def _read_file(self, start_after_log_buffer: bool = False) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.

        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        start_index = self._calculate_start_index() if start_after_log_buffer else 0

        # Find the sampling rate of the raw data packets:
        launch_raw_data_packet_rate = 1 / self.file_metadata["imu_details"]["raw_packet_frequency"]

        collected_data: pl.DataFrame = self._scan_csv(start_index=start_index).collect()

        # Iterate over the rows of the dataframe and put the data packets in the queue
        for row in collected_data.iter_rows(named=True):
            # Check if the loop should stop:
            if not self._requested_to_run.is_set():
                break

            start_time = time.time()

            # Drop None values from the row so msgspec Structs can be made:
            # This approach of deleting is faster than using a dict comprehension by about 6%
            row_dict = row.copy()
            for k in list(row_dict.keys()):
                if row_dict[k] is None:
                    del row_dict[k]

            # If the row has the scaledAccelX field, it is a raw data packet, otherwise it is an
            # estimated data packet
            raw_packet = row_dict.get("scaledAccelX")
            if raw_packet:
                imu_data_packet = RawDataPacket(**row_dict)
            else:
                imu_data_packet = EstimatedDataPacket(**row_dict)

            self._queued_imu_packets.put(imu_data_packet)

            # sleep only if we are running a real-time simulation
            # Our IMU sends raw data at 1000 Hz, so we sleep for 1 ms between each packet to
            # pretend to be real-time
            if not raw_packet:
                continue

            sim_speed = self._sim_speed_factor
            if sim_speed > 0:
                execution_time = time.time() - start_time
                sleep_time = max(0.0, launch_raw_data_packet_rate - execution_time)
                adjusted_sleep_time = sleep_time * (2.0 - sim_speed) / sim_speed
                # See https://github.com/python/cpython/issues/125997 on why we don't
                # time.sleep(0). If we did that, the mocks would be at least 2x slower.
                if adjusted_sleep_time:
                    time.sleep(adjusted_sleep_time)
            else:  # If sim_speed is 0, we sleep in a loop to simulate a hang:
                while not self._sim_speed_factor and self._requested_to_run.is_set():
                    time.sleep(BUSY_WAIT_SECONDS)

    def _fetch_data_loop(
        self,
        start_after_log_buffer: bool = False,
    ) -> None:
        """
        A wrapper function to suppress KeyboardInterrupt exceptions when reading the log file.

        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        self._running.set()  # Specify that the thread is running
        self._read_file(start_after_log_buffer)

        # For the mock, once we're done reading the file, we say it is no longer running
        self._running.clear()
        # If we don't put the STOP_SIGNAL in the queue, the main thread will wait till IMU_TIMEOUT
        # seconds before exiting, which is not what we want.
        self._queued_imu_packets.put(STOP_SIGNAL)

    def get_launch_time(self) -> int:
        """
        Gets the launch time, from reading the csv file.

        :return int: The corresponding launch time in nanoseconds. Returns 0 if the launch time
            could not be found.
        """
        # Read the file, and check when the "state_letter" field shows "M", or when the
        # magnitude of the estimated linear acceleration is greater than 3 m/s^2:

        # We get an exception for files which didn't log any state, e.g. purple_launch.csv
        with contextlib.suppress(Exception):
            df: pl.LazyFrame = pl.scan_csv(self._log_file_path).select(
                ["timestamp", "state_letter"]
            )
            # Check for the "M" state, get only the first timestamp
            launch_time: pl.DataFrame = (
                df.filter(pl.col("state_letter") == "M").select(pl.first("timestamp")).collect()
            )
            if not launch_time.is_empty():
                return convert_to_nanoseconds(launch_time["timestamp"][0])
            return 0

        mag: pl.DataFrame = (
            pl.scan_csv(
                self._log_file_path,
                has_header=True,
            )
            .select(
                [
                    "timestamp",
                    "estLinearAccelX",
                    "estLinearAccelY",
                    "estLinearAccelZ",
                ]
            )
            .with_columns(
                (
                    pl.col("estLinearAccelX") ** 2
                    + pl.col("estLinearAccelY") ** 2
                    + pl.col("estLinearAccelZ") ** 2
                )
                .sqrt()
                .alias("estLinearAccelMag")
            )
            .filter(pl.col("estLinearAccelMag") > 3)
            .select("timestamp")
            .first()
            .collect()
        )

        if not mag.is_empty():
            return convert_to_nanoseconds(mag["timestamp"][0])
        return 0
