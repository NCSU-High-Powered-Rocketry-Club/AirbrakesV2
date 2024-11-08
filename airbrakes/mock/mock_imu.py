"""Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket."""

import contextlib
import csv
import multiprocessing
import time
from pathlib import Path

from airbrakes.data_handling.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from airbrakes.hardware.imu import IMU
from constants import MAX_QUEUE_SIZE, SIMULATION_MAX_QUEUE_SIZE
from utils import convert_to_float, convert_to_nanoseconds


class MockIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns data read from a previous log file.
    """

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
        # Check if the launch data file exists:
        if not log_file_path:
            # Just use the first file in the `launch_data` directory:
            log_file_path = next(iter(Path("launch_data").glob("*.csv")))

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
                log_file_path,
                real_time_simulation,
                start_after_log_buffer,
            ),
            name="Mock IMU Process",
        )

        # Makes a boolean value that is shared between processes
        self._running = multiprocessing.Value("b", False)

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
            with log_file_path.open(newline="") as csvfile:
                reader = csv.DictReader(csvfile)

                # Reads each row as a dictionary
                row: dict[str, str]
                init_timestamp = None
                for idx, row in enumerate(reader):
                    timestamp = convert_to_nanoseconds(row["timestamp"])
                    if init_timestamp is None:
                        init_timestamp = timestamp
                        continue
                    # Anything greater than 1 second is end of the buffer.
                    if timestamp - init_timestamp > 1e9:
                        start_index = idx
                        break
                    init_timestamp = timestamp

        with log_file_path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            # Reads each row as a dictionary
            row: dict[str, str]
            for idx, row in enumerate(reader):
                # If we are starting after the log buffer, skip the rows before the buffer:
                if idx < start_index:
                    continue

                start_time = time.time()

                # Check if the process should stop
                if not self._running.value:
                    break

                imu_data_packet = None
                fields_dict = {}

                scaled_accel_x = row.get("scaledAccelX")  # raw data packet field
                est_linear_accel_x = row.get("estLinearAccelX")  # estimated data packet field
                # Create the data packet based on the row
                if scaled_accel_x:
                    for key in RawDataPacket.__struct_fields__:
                        val = row.get(key, None)
                        if val:
                            fields_dict[key] = convert_to_float(val)
                    fields_dict["timestamp"] = convert_to_nanoseconds(row["timestamp"])
                    imu_data_packet = RawDataPacket(**fields_dict)
                elif est_linear_accel_x:
                    for key in EstimatedDataPacket.__struct_fields__:
                        val = row.get(key, None)
                        if val:
                            fields_dict[key] = convert_to_float(val)
                    fields_dict["timestamp"] = convert_to_nanoseconds(row["timestamp"])
                    imu_data_packet = EstimatedDataPacket(**fields_dict)
                # Accounts for the case that the log file is messed up and has empty rows
                # (or rows not corresponding to any data packet)
                else:
                    continue

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
