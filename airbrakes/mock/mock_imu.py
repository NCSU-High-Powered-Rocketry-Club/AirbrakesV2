"""Module for simulating interacting with the IMU (Inertial measurement unit) on the rocket."""

import csv
import time
from pathlib import Path

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.hardware.imu import IMU


class MockIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware and returns data read
    from a previous log file.
    """

    def __init__(self, log_file_name: str, frequency: int):
        """
        Initializes the object that pretends to be an IMU for testing purposes by reading from a log file.
        :param log_file_name: The name of the log file to read data from.
        :param frequency: The frequency in Hz to read data from the log file.
        """
        super().__init__(log_file_name, frequency)

    def _fetch_data_loop(self, log_file_name: str, frequency: int) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.
        :param log_file_name: the name of the log file to read data from located in logs/
        :param frequency: Frequency in Hz for how often to pretend to fetch data
        """
        # Calculate the interval between readings based on frequency
        # TODO: reading takes a little bit of time, so we should probably subtract a few milliseconds from the interval
        interval = 1.0 / frequency

        # Makes the path to the log file in an os-independent way
        log_file_path = Path("logs") / log_file_name

        with log_file_path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                row: dict[str, str]

                # Check if the process should stop
                if not self._running.value:
                    break

                imu_data_packet = None

                # Create the data packet based on the row
                if row.get("scaledAccelX") is not None:
                    imu_data_packet = RawDataPacket(int(row["timestamp"]))
                    imu_data_packet.scaledAccelX = float(row.get("scaledAccelX"))
                    imu_data_packet.scaledAccelY = float(row.get("scaledAccelY"))
                    imu_data_packet.scaledAccelZ = float(row.get("scaledAccelZ"))
                    imu_data_packet.scaledGyroX = float(row.get("scaledGyroX"))
                    imu_data_packet.scaledGyroY = float(row.get("scaledGyroY"))
                    imu_data_packet.scaledAccelZ = float(row.get("scaledGyroZ"))
                elif row.get("estCompensatedAccelX") is not None:
                    imu_data_packet = EstimatedDataPacket(int(row["timestamp"]))
                    imu_data_packet.estCompensatedAccelX = float(row.get("estCompensatedAccelX"))
                    imu_data_packet.estCompensatedAccelY = float(row.get("estCompensatedAccelY"))
                    imu_data_packet.estCompensatedAccelZ = float(row.get("estCompensatedAccelZ"))
                    imu_data_packet.estAngularRateX = float(row.get("estAngularRateX"))
                    imu_data_packet.estAngularRateY = float(row.get("estAngularRateY"))
                    imu_data_packet.estAngularRateZ = float(row.get("estAngularRateZ"))
                    imu_data_packet.estOrientQuaternionW = float(row.get("estOrientQuaternionW"))
                    imu_data_packet.estOrientQuaternionX = float(row.get("estOrientQuaternionX"))
                    imu_data_packet.estOrientQuaternionY = float(row.get("estOrientQuaternionY"))
                    imu_data_packet.estOrientQuaternionZ = float(row.get("estOrientQuaternionZ"))
                    imu_data_packet.estPressureAlt = float(row.get("estPressureAlt"))
                    imu_data_packet.estAttitudeUncertQuaternionW = float(row.get("estAttitudeUncertQuaternionW"))
                    imu_data_packet.estAttitudeUncertQuaternionX = float(row.get("estAttitudeUncertQuaternionX"))
                    imu_data_packet.estAttitudeUncertQuaternionY = float(row.get("estAttitudeUncertQuaternionY"))
                    imu_data_packet.estAttitudeUncertQuaternionZ = float(row.get("estAttitudeUncertQuaternionZ"))

                if imu_data_packet is None:
                    continue

                # Put the packet in the queue
                self._data_queue.put(imu_data_packet)

                # Simulate polling interval
                time.sleep(interval)
