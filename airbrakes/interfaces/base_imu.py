"""
Module defining the base class (BaseIMU) for interacting with the IMU (Inertial measurement unit) on
the rocket.
"""

import contextlib
import multiprocessing
from multiprocessing import TimeoutError
from multiprocessing.context import ForkServerProcess

import msgspec
from faster_fifo import Empty, Queue

from airbrakes.constants import IMU_TIMEOUT_SECONDS, MAX_FETCHED_PACKETS, STOP_SIGNAL
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)


class BaseIMU:
    """
    Base class for the IMU, MockIMU, and SimIMU classes.
    """

    __slots__ = (
        "_data_fetch_process",
        "_imu_packets_per_cycle",
        "_queued_imu_packets",
        "_running",
    )

    def __init__(self, data_fetch_process: ForkServerProcess, queued_imu_packets: Queue) -> None:
        """
        Initialises object using arguments passed by the constructors of the subclasses.

        :param data_fetch_process: the multiprocessing process for the IMU.
        :param queued_imu_packets: the queue that the IMUDataPackets will be put into and taken
            from.
        """
        self._queued_imu_packets = queued_imu_packets
        self._data_fetch_process = data_fetch_process
        # Makes a boolean value that is shared between processes
        context = multiprocessing.get_context("forkserver")
        self._running = context.Value("b", False, lock=False)
        self._imu_packets_per_cycle = context.Value("i", 0, lock=False)

    def _setup_queue_serialization_method(self) -> None:
        """
        Sets up the serialization methods for the queued IMU packets for faster-fifo.

        This is not done in the __init__ because "spawn" and "forkserver" will attempt to pickle the
        msgpack encoder and decoder, which will fail. Thus, we do it for the main and child process
        after the child has been born.
        """
        self._queued_imu_packets.dumps = msgspec.msgpack.Encoder().encode
        self._queued_imu_packets.loads = msgspec.msgpack.Decoder(
            type=EstimatedDataPacket | RawDataPacket | str
        ).decode

    @property
    def imu_packets_per_cycle(self) -> int:
        """
        :return: The number of data packets fetched from the IMU per iteration. Useful for measuring
        the performance of our loop.
        """
        return self._imu_packets_per_cycle.value

    @property
    def queued_imu_packets(self) -> int:
        """
        Gets the amount of IMU data packets in the multiprocessing queue :return: The number of
        IMUDataPackets in the queue.
        """
        return self._queued_imu_packets.qsize()

    @property
    def is_running(self) -> bool:
        """
        Returns whether the process fetching data from the IMU is running.

        :return: True if the process is running, False otherwise.
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
        self._setup_queue_serialization_method()

    def get_imu_data_packet(self) -> IMUDataPacket | None:
        """
        Gets the last available IMU data packet from the imu packet queue.

        :return: an IMUDataPacket object containing the latest data from the imu packet queue. If a
            value is not available, it will be None.
        """
        return self._queued_imu_packets.get(timeout=IMU_TIMEOUT_SECONDS)

    def get_imu_data_packets(self, block: bool = True) -> list[IMUDataPacket]:
        """
        Returns all available IMU data packets from the queued imu packets.

        :param block: Whether to wait until a IMU data packet is available or not.
        :return: A list containing the latest IMU data packets from the imu packet queue.
        """
        try:
            packets = self._queued_imu_packets.get_many(
                block=block, max_messages_to_get=MAX_FETCHED_PACKETS, timeout=IMU_TIMEOUT_SECONDS
            )
        except Empty:  # If the queue is empty (i.e. timeout hit), don't bother waiting.
            return []
        else:
            if STOP_SIGNAL in packets:  # only used by the MockIMU
                return []  # Makes the main update() loop exit early.
            return packets
