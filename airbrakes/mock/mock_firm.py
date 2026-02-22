"""Module for simulating the FIRM hardware by reading from a log file."""

import queue
import threading
import time
from pathlib import Path

import msgspec
import polars as pl
from firm_client import FIRMDataPacket

import airbrakes.constants
from airbrakes.base_classes.base_firm import BaseFIRM
from airbrakes.constants import FIRM_SERIAL_TIMEOUT_SECONDS, STOP_SIGNAL


class RocketParameters(msgspec.Struct):
    """
    Rocket parameters needed for IMU processing.
    """

    rocket_Cd: float | None
    rocket_mass_kg: float | None
    rocket_cross_sectional_area_m2: float | None


class MockFIRM(BaseFIRM):
    """
    A mock implementation of FIRM for testing/simulation purposes.

    It reads a CSV log file and feeds FIRMDataPackets into the queue as
    if they were coming from the hardware.
    """

    __slots__ = (
        "_data_fetch_thread",
        "_headers",
        "_is_running",
        "_log_file_path",
        "_needed_fields",
        "_queued_packets",
        "_requested_to_run",
        "file_metadata",
        "rocket_parameters",
    )

    def __init__(
        self,
        real_time_replay: bool = False,
        log_file_path: Path | None = None,
        start_after_log_buffer: bool = True,
    ):
        """
        Initializes the MockFIRM.

        :param real_time_replay: If True, packets are emitted with
            delays matching their original timestamps. If False, packets
            are emitted as fast as possible.
        :param log_file_path: Optional path to a specific CSV log file.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        # 1. Resolve Log File Path
        self._log_file_path = log_file_path
        if self._log_file_path is None:
            # Default to finding the first CSV in launch_data
            root_dir = Path(__file__).parent.parent.parent
            launch_data_dir = root_dir / "launch_data"

            # Use glob to find files
            potential_files = list(launch_data_dir.rglob("*.csv"))
            if potential_files:
                self._log_file_path = potential_files[0]
            else:
                self._log_file_path = Path("launch_data/jackpot_launch_1.csv")

        self._log_file_path = self._log_file_path

        file_metadata: dict = MockFIRM.read_file_metadata()
        self.file_metadata = file_metadata.get(self._log_file_path.name, {})
        self.rocket_parameters: RocketParameters = self._get_rocket_parameters(self.file_metadata)

        # Dynamically set rocket parameters in the airbrakes.constants module based on the metadata
        if self.rocket_parameters.rocket_mass_kg is not None:
            airbrakes.constants.ROCKET_DRY_MASS_KG = self.rocket_parameters.rocket_mass_kg
        if self.rocket_parameters.rocket_Cd is not None:
            airbrakes.constants.ROCKET_CD = self.rocket_parameters.rocket_Cd
        if self.rocket_parameters.rocket_cross_sectional_area_m2 is not None:
            airbrakes.constants.ROCKET_CROSS_SECTIONAL_AREA_M2 = (
                self.rocket_parameters.rocket_cross_sectional_area_m2
            )

        # Set up a queue and thread
        self._queued_packets: queue.SimpleQueue[FIRMDataPacket | str] = queue.SimpleQueue()
        self._data_fetch_thread = threading.Thread(
            target=self._fetch_data_loop,
            args=(real_time_replay, start_after_log_buffer),
            name="Mock FIRM Thread",
            daemon=True,
        )

        self._is_running = threading.Event()
        self._requested_to_run = threading.Event()

        super().__init__()

    @property
    def is_running(self) -> bool:
        """
        Returns True if the Mock FIRM thread is running and fetching
        data.
        """
        return self._is_running.is_set()

    @property
    def requested_to_run(self) -> bool:
        """
        Returns True if the Mock FIRM thread has been requested to run.
        """
        return self._requested_to_run.is_set()

    @staticmethod
    def read_file_metadata() -> dict:
        """
        Reads the metadata from the log file and returns it as a dictionary.
        """
        metadata = Path("launch_data/metadata.json")
        return msgspec.json.decode(metadata.read_text())

    def start(self) -> None:
        """Starts the Mock FIRM thread."""
        self._requested_to_run.set()
        if not self._data_fetch_thread.is_alive():
            self._data_fetch_thread.start()

    def stop(self) -> None:
        """Stops the Mock FIRM thread."""
        self._requested_to_run.clear()
        # Fetch all packets which are not yet fetched and discard them, so main() does not get
        # stuck (i.e. deadlocks) waiting for the thread to finish.
        self._queued_packets.put(STOP_SIGNAL)  # signal the main thread to stop waiting

        self._data_fetch_thread.join(timeout=FIRM_SERIAL_TIMEOUT_SECONDS)
        if self._data_fetch_thread.is_alive():
            raise RuntimeError("FIRM data fetch thread did not terminate in time.")

    def get_data_packets(self, block: bool = True) -> list[FIRMDataPacket]:
        """Returns all available FIRM data packets from the queue."""
        packets = []

        if block:
            # Block until at least one item is available
            item = self._queued_packets.get(block=True)
            if item == STOP_SIGNAL:
                return packets  # Makes the main update() loop exit early.
            packets.append(item)

        while not self._queued_packets.empty():
            item = self._queued_packets.get(block=block)

            # If we hit the stop signal, ensure we mark ourselves as stopped
            if item == STOP_SIGNAL:
                break  # Makes the main update() loop exit early.

            packets.append(item)

        return packets

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

    # ------------------------ THREAD METHODS -------------------------

    def _scan_csv(self, *, start_index: int = 0, **kwargs) -> pl.LazyFrame:
        """Prepares the Polars LazyFrame with only the columns we need."""
        # 1. Get all headers present in the CSV
        self._headers = pl.scan_csv(self._log_file_path).collect_schema().names()

        # 2. Get all fields defined in the FIRMDataPacket struct
        packet_fields = list(FIRMDataPacket.__struct_fields__)

        # 3. Intersection: Only read columns that exist in both the CSV and the Packet
        self._needed_fields = [f for f in packet_fields if f in self._headers]

        return pl.scan_csv(
            self._log_file_path,
            has_header=True,
            skip_rows_after_header=start_index,
            infer_schema_length=100,
            **kwargs,
        ).select(self._needed_fields)

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
        Reads the CSV, converts rows to FIRMDataPackets, and manages replay
        timing.

        :param real_time_replay: Whether to mimic a real flight by sleeping for a set period, or run
            at full speed, e.g. for using it in the CI.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        start_index = self._calculate_start_index() if start_after_log_buffer else 0

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

            firm_data_packet = FIRMDataPacket(**row_dict)

            self._queued_packets.put(firm_data_packet)

            # Sleep only if we are running a real-time replay
            if real_time_replay:
                # Mimic the polling interval so it "runs in real time"
                end_time = time.time()
                time.sleep(max(0.0, launch_raw_data_packet_rate - (end_time - start_time)))

    def _fetch_data_loop(
        self,
        real_time_replay: bool,
        start_after_log_buffer: bool = False,
    ) -> None:
        """
        :param real_time_replay: Whether to mimic a real flight by sleeping for a set period, or run
            at full speed.
        :param start_after_log_buffer: Whether to send the data packets only after the log buffer
            was filled for Standby state.
        """
        """The main thread loop."""
        self._is_running.set()

        self._read_file(real_time_replay, start_after_log_buffer)

        self._is_running.clear()
        # If we don't put the STOP_SIGNAL in the queue, the main thread will wait till
        # FIRM_SERIAL_TIMEOUT seconds before exiting, which is not what we want.
        self._queued_packets.put(STOP_SIGNAL)
