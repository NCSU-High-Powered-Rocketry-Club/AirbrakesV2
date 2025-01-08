"""Module defining the base class (BaseIMU) for interacting with
the IMU (Inertial measurement unit) on the rocket."""

import collections
import contextlib
import multiprocessing

from airbrakes.data_handling.imu_data_packet import (
    IMUDataPacket,
)
from constants import IMU_TIMEOUT_SECONDS


class BaseIMU:
    """
    Base class for the IMU and MockIMU classes.
    """

    __slots__ = (
        "_data_fetch_process",
        "_data_queue",
        "_running",
    )

    def __init__(
        self, data_fetch_process: multiprocessing.Process, data_queue: multiprocessing.Queue
    ) -> None:
        """
        Initialises object using arguments passed by the constructors of the subclasses.
        """
        self._data_fetch_process = data_fetch_process
        self._data_queue = data_queue
        # Makes a boolean value that is shared between processes
        self._running = multiprocessing.Value("b", False)

    def stop(self) -> None:
        """
        Stops the process separate from the main process for fetching data from the IMU.
        """
        self._running.value = False
        # Fetch all packets which are not yet fetched and discard them, so main() does not get
        # stuck (i.e. deadlocks) waiting for the process to finish. A more technical explanation:
        # Case 1: .put() is blocking and if the queue is full, it keeps waiting for the queue to
        # be empty, and thus the process never .joins().
        # Case 2: The other process finishes up before we call the below method, so there might be
        # nothing in the queue, and then calling get_imu_data_packet() will block the main process
        # indefinitely (that's why there's a timeout in the get_imu_data_packet() method).
        with contextlib.suppress(multiprocessing.TimeoutError):
            self.get_imu_data_packets()
            self._data_fetch_process.join(timeout=IMU_TIMEOUT_SECONDS)

    def start(self) -> None:
        """
        Starts the process separate from the main process for fetching data from the IMU.
        """
        self._running.value = True
        self._data_fetch_process.start()

    def get_imu_data_packet(self) -> IMUDataPacket | None:
        """
        Gets the last available data packet from the IMU.
        :return: an IMUDataPacket object containing the latest data from the IMU. If a value is not
        available, it will be None.
        """
        return self._data_queue.get(timeout=IMU_TIMEOUT_SECONDS)

    def get_imu_data_packets(self) -> collections.deque[IMUDataPacket]:
        """
        Returns all available data packets from the IMU.
        :return: A deque containing the specified number of data packets
        """
        # We use a deque because it's faster than a list for popping from the left
        data_packets = collections.deque()
        # While there is data in the queue, get the data packet and add it to the dequeue which we
        # return
        while not self._data_queue.empty():
            data_packets.append(self.get_imu_data_packet())

        return data_packets

    @property
    def is_running(self) -> bool:
        """
        Returns whether the process fetching data from the IMU is running.
        :return: True if the process is running, False otherwise
        """
        return self._running.value
