"""
Module defining the base class (BaseIMU) for interacting with the IMU (Inertial measurement unit) on
the rocket.
"""

import threading
from typing import TYPE_CHECKING

from airbrakes import utils
from airbrakes.constants import IMU_TIMEOUT_SECONDS, STOP_SIGNAL

if TYPE_CHECKING:
    import queue
    from pathlib import Path

    from airbrakes.data_handling.packets.imu_data_packet import IMUDataPacket


class BaseIMU:
    """
    A base class for IMU devices that defines the interface for fetching data packets and provides
    common functionality for mock and real IMU devices.
    """

    __slots__ = (
        "_data_fetch_thread",
        "_imu_packets_per_cycle",
        "_queued_imu_packets",
        "_requested_to_run",
        "_running",
    )

    def __init__(
        self, data_fetch_thread: threading.Thread, queued_imu_packets: queue.SimpleQueue
    ) -> None:
        """
        Initialises object using arguments passed by the constructors of the subclasses.

        :param data_fetch_thread: Thread used for fetching IMU data.
        :param queued_imu_packets: The queue that the IMUDataPackets will be put into and taken
                                   from.
        """
        self._queued_imu_packets = queued_imu_packets
        self._data_fetch_thread = data_fetch_thread
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
        Returns the number of data packets fetched from the IMU per iteration. Useful for measuring
        the performance of our loop.
        """
        return self._imu_packets_per_cycle

    @property
    def queued_imu_packets(self) -> int:
        """
        Returns the number of IMUDataPackets in the queue.
        """
        return self._queued_imu_packets.qsize()

    @property
    def is_running(self) -> bool:
        """
        Returns whether the thread fetching data from the IMU is running.

        :return: True if the thread is running, False otherwise.
        """
        return self._running.is_set()

    @property
    def log_file_path(self) -> Path | None:
        """
        Returns the replay log path for mock devices, or None for real devices.
        """
        return None

    def stop(self) -> None:
        """
        Stops the IMU data-fetch thread.

        :raises RuntimeError: If the IMU data fetch thread does not terminate in configured
                              timeout.
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
        Starts the IMU data-fetch thread.
        """
        self._requested_to_run.set()
        self._data_fetch_thread.start()

    def get_imu_data_packets(self, block: bool = True) -> list[IMUDataPacket]:
        """
        Returns all available IMU data packets from the queued IMU packets.

        :param block: Whether to wait until a IMU data packet is available or not.
        :return: A list containing the latest IMU data packets from the IMU packet queue.
        """
        packets = []
        packets.extend(utils.get_all_packets_from_queue(self._queued_imu_packets, block=block))
        if STOP_SIGNAL in packets:
            return []
        return packets
