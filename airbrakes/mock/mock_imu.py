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

        # Makes the path to the log file in an os-independent way
        log_file_path = Path("logs") / log_file_name

        with log_file_path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            # Reads each row as a dictionary
            for row in reader:
                row: dict[str, str]

                start_time = time.time()

                # Check if the process should stop
                if not self._running.value:
                    break

                imu_data_packet = None

                # Create the data packet based on the row
                if row.get("scaledAccelX") is not None and row.get("scaledAccelX") != "":
                    imu_data_packet = RawDataPacket(self._convert_to_nanoseconds(row["timestamp"]))
                    imu_data_packet.scaledAccelX = self._convert_to_float(row.get("scaledAccelX"))
                    imu_data_packet.scaledAccelY = self._convert_to_float(row.get("scaledAccelY"))
                    imu_data_packet.scaledAccelZ = self._convert_to_float(row.get("scaledAccelZ"))
                    imu_data_packet.scaledGyroX = self._convert_to_float(row.get("scaledGyroX"))
                    imu_data_packet.scaledGyroY = self._convert_to_float(row.get("scaledGyroY"))
                    imu_data_packet.scaledAccelZ = self._convert_to_float(row.get("scaledGyroZ"))
                elif row.get("estLinearAccelX") is not None and row.get("estLinearAccelX") != "":
                    imu_data_packet = EstimatedDataPacket(self._convert_to_nanoseconds(row["timestamp"]))
                    imu_data_packet.estCompensatedAccelX = self._convert_to_float(row.get("estCompensatedAccelX", 0.0))
                    imu_data_packet.estCompensatedAccelY = self._convert_to_float(row.get("estCompensatedAccelY", 0.0))
                    imu_data_packet.estCompensatedAccelZ = self._convert_to_float(row.get("estCompensatedAccelZ", 0.0))
                    imu_data_packet.estLinearAccelX = self._convert_to_float(row.get("estLinearAccelX"))
                    imu_data_packet.estLinearAccelY = self._convert_to_float(row.get("estLinearAccelY"))
                    imu_data_packet.estLinearAccelZ = self._convert_to_float(row.get("estLinearAccelZ"))
                    imu_data_packet.estAngularRateX = self._convert_to_float(row.get("estAngularRateX"))
                    imu_data_packet.estAngularRateY = self._convert_to_float(row.get("estAngularRateY"))
                    imu_data_packet.estAngularRateZ = self._convert_to_float(row.get("estAngularRateZ"))
                    imu_data_packet.estOrientQuaternionW = self._convert_to_float(row.get("estOrientQuaternionW"))
                    imu_data_packet.estOrientQuaternionX = self._convert_to_float(row.get("estOrientQuaternionX"))
                    imu_data_packet.estOrientQuaternionY = self._convert_to_float(row.get("estOrientQuaternionY"))
                    imu_data_packet.estOrientQuaternionZ = self._convert_to_float(row.get("estOrientQuaternionZ"))
                    imu_data_packet.estPressureAlt = self._convert_to_float(row.get("estPressureAlt"))
                    imu_data_packet.estAttitudeUncertQuaternionW = self._convert_to_float(row.get("estAttitudeUncertQuaternionW"))
                    imu_data_packet.estAttitudeUncertQuaternionX = self._convert_to_float(row.get("estAttitudeUncertQuaternionX"))
                    imu_data_packet.estAttitudeUncertQuaternionY = self._convert_to_float(row.get("estAttitudeUncertQuaternionY"))
                    imu_data_packet.estAttitudeUncertQuaternionZ = self._convert_to_float(row.get("estAttitudeUncertQuaternionZ"))

                if imu_data_packet is None:
                    continue

                # Put the packet in the queue
                self._data_queue.put(imu_data_packet)

                end_time = time.time()

                # Sleep 1 ms after every raw data packet, but don't sleep after an estimated data packet
                if isinstance(imu_data_packet, RawDataPacket):
                    # Simulate polling interval
                    time.sleep(max(0, 0.001 - (end_time - start_time)))

    def _convert_to_nanoseconds(self, value) -> int:
        if isinstance(value, float):
            # Convert seconds to nanoseconds
            nanoseconds = value * 1e9
            return int(nanoseconds)  # Convert to integer if needed
        else:
            return value  # Assume that it is in nanoseconds


    def _convert_to_float(self, value) -> float | None:
        try:
            float_value = float(value)  # Attempt to convert to float
            return float_value  
        except (ValueError, TypeError):
            return None  # Return None if the conversion fails


