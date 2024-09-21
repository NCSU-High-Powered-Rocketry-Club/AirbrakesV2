"""Module for interacting with the IMU (Inertial measurement unit) on the rocket."""

import collections
import csv
import multiprocessing
import time
import warnings
from abc import ABC, abstractmethod
from pathlib import Path

try:
    import mscl
except ImportError:
    warnings.warn(
        "Could not import MSCL, IMU will not work. Please see installation instructions"
        "here: https://github.com/LORD-MicroStrain/MSCL/tree/master",
        stacklevel=2,
    )

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket
from constants import ESTIMATED_DESCRIPTOR_SET, MAX_QUEUE_SIZE, RAW_DESCRIPTOR_SET


class AbstractIMU(ABC):
    """
    Abstract base class for interacting with the IMU (Inertial Measurement Unit) on the rocket.
    Any IMU implementation should inherit from this class and implement the necessary methods to start, stop, and
    retrieve data from the IMU.
    """

    __slots__ = (
        "_data_fetch_process",
        "_data_queue",
        "_running",
        "frequency",
        "upside_down",
    )

    @abstractmethod
    def __init__(self, frequency: int):
        """
        Initializes the IMU object.
        :param frequency: The frequency in Hz that the IMU will be polled at.
        """
        self.frequency = frequency

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """
        Returns whether the process fetching data from the IMU is running.
        """
        return self._running.value

    @abstractmethod
    def start(self) -> None:
        """
        Starts the process fetching data from the IMU.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stops the process fetching data from the IMU. This should be called when the program is shutting down.
        """

    @abstractmethod
    def get_imu_data_packet(self) -> IMUDataPacket | None:
        """
        Gets the last available data packet from the IMU.

        Note: If `get_imu_data_packet` is called slower than the frequency set, the data will not
        be the latest, but the first in the queue.

        :return: an IMUDataPacket object containing the latest data from the IMU. If a value is
            not available, it will be None.
        """

    @abstractmethod
    def get_imu_data_packets(self) -> collections.deque[IMUDataPacket]:
        """Returns all available data packets from the IMU.

        :return: A deque containing the specified number of data packets
        """


class IMU(AbstractIMU):
    """
    Represents the IMU on the rocket. It's used to get the current acceleration of the rocket. This is used to interact
    with the data collected by the Parker-LORD 3DMCX5-AR.

    It uses multiprocessing rather than threading to truly run in parallel with the main loop. We're doing this is
    because the IMU constantly polls data and can be slow, so it's better to run it in parallel.

    Here is the setup docs: https://github.com/LORD-MicroStrain/MSCL/blob/master/HowToUseMSCL.md
    """

    def __init__(self, port: str, frequency: int, upside_down: bool):
        super().__init__(frequency)
        # Shared Queue which contains the latest data from the IMU. The MAX_QUEUE_SIZE is there
        # to prevent memory issues. Realistically, the queue size never exceeds 50 packets when
        # it's being logged.
        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue(MAX_QUEUE_SIZE)
        self._running = multiprocessing.Value("b", False)  # Makes a boolean value that is shared between processes

        # Starts the process that fetches data from the IMU
        self._data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop, args=(port, self.frequency)
        )

    @property
    def is_running(self) -> bool:
        return super().is_running

    def start(self) -> None:
        self._running.value = True
        self._data_fetch_process.start()

    def stop(self) -> None:
        self._running.value = False
        # Waits for the process to finish before stopping it
        self._data_fetch_process.join()

    def get_imu_data_packet(self) -> IMUDataPacket | None:
        return self._data_queue.get()

    def get_imu_data_packets(self) -> collections.deque[IMUDataPacket]:
        """Returns all available data packets from the IMU.

        :return: A deque containing the specified number of data packets
        """

        data_packets = collections.deque()

        while not self._data_queue.empty():
            data_packet = self.get_imu_data_packet()
            data_packets.append(data_packet)

        return data_packets

    def _fetch_data_loop(self, port: str, frequency: int) -> None:
        """
        The loop that fetches data from the IMU. It runs in parallel with the main loop.
        :param port: the port that the IMU is connected to
        :param frequency: the frequency in Hz that the IMU will be polled at
        """
        # Connect to the IMU
        connection = mscl.Connection.Serial(port)
        node = mscl.InertialNode(connection)
        timeout = int(1000 / frequency)

        while self._running.value:
            # Get the latest data packets from the IMU, with the help of `getDataPackets`.
            # `getDataPackets` accepts a timeout in milliseconds.
            # During IMU configuration (outside of this code), we set the sampling rate of the IMU
            # as 1ms for RawDataPackets, and 2ms for EstimatedDataPackets.
            # So we use a timeout of 1000 / frequency = 10ms which should be more
            # than enough. If the timeout is hit, the function will return an empty list.

            packets: mscl.MipDataPackets = node.getDataPackets(timeout)
            # Every loop iteration we get the latest data in form of packets from the imu
            for packet in packets:
                # The data packet from the IMU:
                packet: mscl.MipDataPacket

                # Get the timestamp of the packet
                timestamp = packet.collectedTimestamp().nanoseconds()

                # Initialize packet with the timestamp, determines if the packet is raw or estimated
                if packet.descriptorSet() == ESTIMATED_DESCRIPTOR_SET:
                    imu_data_packet = EstimatedDataPacket(timestamp)
                elif packet.descriptorSet() == RAW_DESCRIPTOR_SET:
                    imu_data_packet = RawDataPacket(timestamp)
                else:
                    # This is an unknown packet, so we skip it
                    continue

                # Each of these packets has multiple data points
                for data_point in packet.data():
                    data_point: mscl.MipDataPoint
                    if data_point.valid():
                        channel = data_point.channelName()
                        # This cpp file was the only place I was able to find all the channel names
                        # https://github.com/LORD-MicroStrain/MSCL/blob/master/MSCL/source/mscl/MicroStrain/MIP/MipTypes.cpp
                        # Check if the channel name is one we want to save
                        if hasattr(imu_data_packet, channel) or "Quaternion" in channel:
                            # First checks if the data point needs special handling, if not, just set the attribute
                            match channel:
                                # These specific data points are matrix's rather than doubles
                                case "estAttitudeUncertQuaternion" | "estOrientQuaternion":
                                    # This makes a 4x1 matrix from the data point with the data as [[x], [y], [z], [w]]
                                    matrix = data_point.as_Matrix()
                                    # Sets the X, Y, Z, and W of the quaternion to the data packet object
                                    setattr(imu_data_packet, f"{channel}X", matrix.as_floatAt(0, 0))
                                    setattr(imu_data_packet, f"{channel}Y", matrix.as_floatAt(0, 1))
                                    setattr(imu_data_packet, f"{channel}Z", matrix.as_floatAt(0, 2))
                                    setattr(imu_data_packet, f"{channel}W", matrix.as_floatAt(0, 3))
                                case _:
                                    # Because the attribute names in our data packet classes are the same as the channel
                                    # names, we can just set the attribute to the value of the data point.
                                    setattr(imu_data_packet, channel, data_point.as_float())

                # Put the latest data into the shared queue
                self._data_queue.put(imu_data_packet)


class MockIMU(AbstractIMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware and returns data read
    from a previous log file.
    """

    __slots__ = ("log_file_path",)

    def __init__(self, log_file_path: Path, frequency: int):
        super().__init__(frequency)
        self.log_file_path = log_file_path

        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue(MAX_QUEUE_SIZE)
        self._running = multiprocessing.Value("b", False)

        # Starts the process that fetches data from the IMU
        self._data_fetch_process = multiprocessing.Process(
            target=self._read_data_loop, args=(self.log_file_path, self.frequency, self.upside_down)
        )

    @property
    def is_running(self) -> bool:
        return super().is_running

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def get_imu_data_packet(self) -> IMUDataPacket | None:
        pass

    def get_imu_data_packets(self) -> collections.deque[IMUDataPacket]:
        pass

    def _read_data_loop(self, log_file_path: Path, frequency: int) -> None:
        """
        Reads the data from the log file and puts it into the shared queue.
        :param log_file_path: Path to the CSV file containing IMU data.
        :param frequency: Frequency in Hz for how often to fetch data.l
        """
        # Calculate the interval between readings based on frequency
        # TODO: reading takes a little bit of time, so we should probably subtract a few milliseconds from the interval
        interval = 1.0 / frequency

        with log_file_path.open(newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
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
