"""Module defining the base class (BaseIMU) for interacting with
the IMU (Inertial measurement unit) on the rocket."""

import contextlib
import sys

from airbrakes.constants import IMU_TIMEOUT_SECONDS, MAX_FETCHED_PACKETS, STOP_SIGNAL
from airbrakes.telemetry.packets.imu_data_packet import (
    IMUDataPacket,
)

# If we are not on windows, we can use the faster_fifo library to speed up the queue operations
if sys.platform != "win32":
    from faster_fifo import Empty, Queue
else:
    from multiprocessing import Queue
    from queue import Empty

from multiprocessing import Process, TimeoutError, Value


class BaseIMU:
    """
    Base class for the IMU and MockIMU classes.
    """

    __slots__ = (
        "_data_fetch_process",
        "_data_queue",
        "_fetched_imu_packets",
        "_running",
    )

    def __init__(self, data_fetch_process: Process, data_queue: Queue) -> None:
        """
        Initialises object using arguments passed by the constructors of the subclasses.
        """
        self._data_fetch_process = data_fetch_process
        self._data_queue = data_queue
        # Makes a boolean value that is shared between processes
        self._running = Value("b", False)
        self._fetched_imu_packets = Value("i", 0)

    @property
    def fetched_imu_packets(self) -> int:
        """
        :return: The number of data packets fetched from the IMU per iteration. Useful for measuring
        the performance of our loop.
        """
        return self._fetched_imu_packets.value

    @property
    def queue_size(self) -> int:
        """
        :return: The number of data packets in the queue.
        """
        return self._data_queue.qsize()

    @property
    def is_running(self) -> bool:
        """
        Returns whether the process fetching data from the IMU is running.
        :return: True if the process is running, False otherwise
        """
        return self._running.value

    def stop(self) -> None:
        """
        Stops the process separate from the main process for fetching data from the IMU.
        """
        self._running.value = False
        # Fetch all packets which are not yet fetched and discard them, so main() does not get
        # stuck (i.e. deadlocks) waiting for the process to finish. A more technical explanation:
        # Case 1: .put() is blocking and if the queue is full, it keeps waiting for the queue to
        # be empty, and thus the process never .joins().
        self.get_imu_data_packets(block=False)
        with contextlib.suppress(TimeoutError):
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

    def get_imu_data_packets(self, block: bool = True) -> list[IMUDataPacket]:
        """
        Returns all available data packets from the IMU.
        :return: A list containing the latest data packets from the IMU.
        """
        try:
            packets = self._data_queue.get_many(
                block=block, max_messages_to_get=MAX_FETCHED_PACKETS, timeout=IMU_TIMEOUT_SECONDS
            )
        except Empty:  # If the queue is empty (i.e. timeout hit), don't bother waiting.
            return []
        else:
            if STOP_SIGNAL in packets:  # only used by the MockIMU
                return []
            return packets
