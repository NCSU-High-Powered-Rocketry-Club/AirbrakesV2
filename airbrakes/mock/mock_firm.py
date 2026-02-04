"""
Module for simulating the FIRM hardware by reading from a log file.
"""

import queue
import threading
import time
import typing
from pathlib import Path

import polars as pl

from airbrakes.base_classes.base_firm import BaseFIRM
from airbrakes.constants import STOP_SIGNAL
from firm_client import FIRMDataPacket


class MockFIRM(BaseFIRM):
    """
    A mock implementation of the FIRM for testing/simulation purposes.

    It reads a CSV log file and feeds FIRMDataPackets into the queue as if they
    were coming from the hardware.
    """

    __slots__ = (
        "_headers",
        "_log_file_path",
        "_needed_fields",
        "_queued_packets",
        "_data_fetch_thread",
        "_running",
    )

    def __init__(
        self,
        real_time_replay: bool = False,
        log_file_path: Path | None = None,
    ):
        """
        Initializes the MockFIRM.

        :param real_time_replay: If True, packets are emitted with delays matching
        their original timestamps. If False, packets are emitted as fast as possible.
        :param log_file_path: Optional path to a specific CSV log file.
        """
        # 1. Resolve Log File Path
        self._log_file_path = log_file_path
        if self._log_file_path is None:
            # Default to finding the first CSV in launch_data
            root_dir = Path(__file__).parent.parent.parent
            launch_data_dir = root_dir / "launch_data"

            # Use glob to find files
            potential_files = list(launch_data_dir.glob("*.csv"))
            if potential_files:
                self._log_file_path = potential_files[0]
            else:
                self._log_file_path = Path("launch_data/shake_n_bake.csv")

        self._log_file_path = typing.cast(Path, self._log_file_path)

        # Set up a queue and thread
        self._queued_packets: queue.SimpleQueue[FIRMDataPacket | str] = queue.SimpleQueue()

        self._data_fetch_thread = threading.Thread(
            target=self._fetch_data_loop,
            args=(real_time_replay,),
            name="Mock FIRM Thread",
            daemon=True,
        )

        super().__init__()

    @property
    def is_running(self) -> bool:
        """
        Returns True if the Mock FIRM thread is running and fetching data.
        """
        return self._running.is_set()

    def start(self) -> None:
        """
        Starts the Mock FIRM thread.
        """
        super().start()
        if not self._data_fetch_thread.is_alive():
            self._data_fetch_thread.start()

    def stop(self) -> None:
        """
        Stops the Mock FIRM thread.
        """
        super().stop()
        # The thread will exit its loop when self._running is cleared

    def get_data_packets(self) -> list[FIRMDataPacket]:
        """
        Returns all available FIRM data packets from the queue.
        """
        packets = []
        while not self._queued_packets.empty():
            item = self._queued_packets.get()

            # If we hit the stop signal, ensure we mark ourselves as stopped
            if item == STOP_SIGNAL:
                self._running.clear()
                break

            packets.append(item)

        return packets

    # ------------------------ THREAD METHODS -------------------------

    def _scan_csv(self) -> pl.LazyFrame:
        """
        Prepares the Polars LazyFrame with only the columns we need.
        """
        # 1. Get all headers present in the CSV
        self._headers = pl.scan_csv(self._log_file_path).collect_schema().names()

        # 2. Get all fields defined in the FIRMDataPacket struct
        packet_fields = list(FIRMDataPacket.__struct_fields__)

        # 3. Intersection: Only read columns that exist in both the CSV and the Packet
        self._needed_fields = [f for f in packet_fields if f in self._headers]

        return pl.scan_csv(
            self._log_file_path,
            has_header=True,
            infer_schema_length=1000,  # Scan more rows to infer types correctly
        ).select(self._needed_fields)

    def _read_file(self, real_time_replay: bool) -> None:
        """
        Reads the CSV, converts rows to FIRMDataPackets, and manages replay timing.
        """
        try:
            # Collect the dataframe
            collected_data: pl.DataFrame = self._scan_csv().collect()
        except Exception:
            # If file is empty or missing, just return
            return

        prev_timestamp = None

        # Iterate over every row
        for row in collected_data.iter_rows(named=True):
            if not self._running.is_set():
                break

            loop_start_time = time.time()

            # 1. Clean Data: Remove None values so msgspec doesn't complain
            row_dict = {k: v for k, v in row.items() if v is not None}

            # 2. Create Packet
            try:
                packet = FIRMDataPacket(**row_dict)
                self._queued_packets.put(packet)
            except Exception:
                # If a row is malformed, skip it
                continue

            # 3. Replay Logic
            if real_time_replay:
                current_timestamp = getattr(packet, "timestamp_seconds", None)

                # We can only sleep if we have a current and previous timestamp
                if current_timestamp is not None and prev_timestamp is not None:
                    # Calculate gap in the recording
                    delta_log = current_timestamp - prev_timestamp

                    # Calculate how long we took to process this loop
                    delta_proc = time.time() - loop_start_time

                    # Sleep the difference
                    sleep_time = max(0.0, delta_log - delta_proc)
                    time.sleep(sleep_time)

                # If we don't have timestamps, but requested real_time,
                # we assume a default rate (e.g. 50Hz -> 0.02s)
                elif current_timestamp is None:
                    time.sleep(0.02)

                prev_timestamp = current_timestamp

    def _fetch_data_loop(self, real_time_replay: bool) -> None:
        """
        The main thread loop.
        """
        self._running.set()

        try:
            self._read_file(real_time_replay)
        except Exception as e:
            print(f"MockFIRM Error reading file: {e}")
        finally:
            self._running.clear()
            self._queued_packets.put(STOP_SIGNAL)
