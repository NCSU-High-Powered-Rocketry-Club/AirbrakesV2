"""Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket."""

import csv
import multiprocessing
import signal
import time
from pathlib import Path

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket
from airbrakes.hardware.imu import IMU
from constants import MAX_QUEUE_SIZE, NOT_REAL_TIME_MAX_QUEUE_SIZE
from utils import convert_to_float, convert_to_nanoseconds


class MockIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware and returns data read
    from a previous log file.
    """

    __slots__ = ()

    def __init__(self, log_file_path: Path, real_time_simulation: bool):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a log file.
        :param log_file_path: The name of the log file to read data from.
        :param real_time_simulation: Whether to simulate a real flight by sleeping for a set period, or run at full
        speed, e.g. for using it in the CI.
        """
        # We don't call the parent constructor as the IMU class has different parameters, so we manually start the
        # process that fetches data from the log file

        # If it's not a real time sim, we limit how big the queue gets when doing an integration test,
        # because we read the file much faster than update(), sometimes resulting thousands of data packets in
        # the queue, which will obviously mess up data processing calculations. We limit it to 15 packets, which
        # is more realistic for a real flight.
        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue(
            MAX_QUEUE_SIZE if real_time_simulation else NOT_REAL_TIME_MAX_QUEUE_SIZE
        )
        self._running = multiprocessing.Value("b", False)  # Makes a boolean value that is shared between processes

        # Starts the process that fetches data from the IMU
        self._data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop, args=(log_file_path, real_time_simulation), name="Mock IMU Process"
        )

    def _fetch_data_loop(self, log_file_path: Path, real_time_simulation: bool) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.
        :param log_file_path: the name of the log file to read data from located in logs/
        :param real_time_simulation: Whether to simulate a real flight by sleeping for a set period, or run at full
        speed, e.g. for using it in the CI.
        """
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignore the KeyboardInterrupt signal

        # Opens the log file
        with log_file_path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            # Reads each row as a dictionary
            row: dict[str, str]
            for row in reader:
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
                    # If the row has the scaledAccelX field, then it's a raw data packet
                    for key in RawDataPacket.__struct_fields__:
                        if val := row.get(key, None):
                            fields_dict[key] = convert_to_float(val)
                    fields_dict["timestamp"] = convert_to_nanoseconds(row["timestamp"])
                    imu_data_packet = RawDataPacket(**fields_dict)
                elif est_linear_accel_x:
                    # If the row has the estLinearAccelX field, then it's an estimated data packet
                    for key in EstimatedDataPacket.__struct_fields__:
                        if val := row.get(key, None):
                            fields_dict[key] = convert_to_float(val)
                    fields_dict["timestamp"] = convert_to_nanoseconds(row["timestamp"])
                    imu_data_packet = EstimatedDataPacket(**fields_dict)

                # Accounts for the case that the log file is messed up and has empty rows (or rows not corresponding to
                # any data packet)
                else:
                    continue

                # Put the packet in the queue
                self._data_queue.put(imu_data_packet)

                # sleep only if we are running a real-time simulation
                # Our IMU sends raw data at 1000 Hz, so we sleep for 1 ms between each packet to pretend to be real-time
                if real_time_simulation and isinstance(imu_data_packet, RawDataPacket):
                    # Simulate polling interval
                    end_time = time.time()
                    time.sleep(max(0.0, 0.001 - (end_time - start_time)))
