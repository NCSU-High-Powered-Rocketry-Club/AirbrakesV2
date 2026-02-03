"""
Module defining the base class (BaseIMU) for interacting with the IMU (Inertial measurement unit) on
the rocket.
"""

import queue
import threading
from typing import TYPE_CHECKING

from airbrakes import utils
from airbrakes.constants import IMU_TIMEOUT_SECONDS, STOP_SIGNAL

if TYPE_CHECKING:
    import queue

    from airbrakes.telemetry.packets.imu_data_packet import (
        IMUDataPacket,
    )


class BaseIMU:
    """
    Base class for the IMU, MockIMU, and SimIMU classes.
    """

    __slots__ = (
        "_data_fetch_thread",
        "_imu_packets_per_cycle",
        "_queued_imu_packets",
        "_requested_to_run",
        "_running",
    )

    def __init__(self, data_fetch_thread: threading.Thread, queued_imu_packets: queue.SimpleQueue):
        """
        Initialises object using arguments passed by the constructors of the subclasses.

        :param data_fetch_thread: the threading thread for the IMU.
        :param queued_imu_packets: the queue that the IMUDataPackets will be put into and taken
            from.
        """
        self._queued_imu_packets = queued_imu_packets
        self._data_fetch_thread = data_fetch_thread
        # Makes a boolean value that is shared between processes
        self._requested_to_run = threading.Event()
        self._running = threading.Event()
        self._imu_packets_per_cycle = 0

    @property
    def requested_to_run(self) -> bool:
        """
        Returns whether the thread fetching data from the IMU has been requested to run.

        :return: True if the thread is requested to run, False otherwise.
        """
        return self._requested_to_run.is_set()

    @property
    def imu_packets_per_cycle(self) -> int:
        """
        :return: The number of data packets fetched from the IMU per iteration. Useful for measuring
        the performance of our loop.
        """
        return self._imu_packets_per_cycle

    @property
    def queued_imu_packets(self) -> int:
        """
        Gets the amount of IMU data packets in the queue.

        :return: The number of IMUDataPackets in the queue.
        """
        return self._queued_imu_packets.qsize()

    @property
    def is_running(self) -> bool:
        """
        Returns whether the thread fetching data from the IMU is running.

        :return: True if the thread is running, False otherwise.
        """
        return self._running.is_set()

    def stop(self) -> None:
        """
        Stops the thread separate from the main thread for fetching data from the IMU.
        """
        self._requested_to_run.clear()
        # Fetch all packets which are not yet fetched and discard them, so main() does not get
        # stuck (i.e. deadlocks) waiting for the thread to finish.
        # self.get_imu_data_packets(block=False)
        self._queued_imu_packets.put(STOP_SIGNAL)  # signal the main thread to stop waiting

        self._data_fetch_thread.join(timeout=IMU_TIMEOUT_SECONDS)
        if self._data_fetch_thread.is_alive():
            raise RuntimeError("IMU data fetch thread did not terminate in time.")

    def start(self) -> None:
        """
        Starts the thread separate from the main thread for fetching data from the IMU.
        """
        self._requested_to_run.set()
        self._data_fetch_thread.start()

    def get_imu_data_packet(self, block: bool = True) -> IMUDataPacket | None:
        """
        Gets the last available IMU data packet from the IMU packet queue.

        :param block: Whether to wait until a IMU data packet is available or not. Will wait up to
            IMU_TIMEOUT_SECONDS seconds.
        :return: an IMUDataPacket object containing the latest data from the IMU packet queue. If a
            value is not available, it will be None.
        :raises queue.Empty: If no IMU data packet is available within the timeout period.
        """
        return self._queued_imu_packets.get(block, timeout=IMU_TIMEOUT_SECONDS)

    def get_imu_data_packets(self, block: bool = True) -> list[IMUDataPacket]:
        """
        Returns all available IMU data packets from the queued IMU packets.

        :param block: Whether to wait until a IMU data packet is available or not.
        :return: A list containing the latest IMU data packets from the IMU packet queue.
        """
        packets = []
        packets.extend(utils.get_all_packets_from_queue(self._queued_imu_packets, block=block))
        if STOP_SIGNAL in packets:  # only used by the MockIMU
            return []  # Makes the main update() loop exit early.
        return packets
