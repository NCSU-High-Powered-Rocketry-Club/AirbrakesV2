"""Module for simulating the IMU on the rocket using generated data."""

import contextlib
import multiprocessing
import time

from airbrakes.data_handling.imu_data_packet import (
    IMUDataPacket,
)
from airbrakes.hardware.imu import IMU
from constants import MAX_QUEUE_SIZE
from simulator.data_gen import DataGenerator


class SimIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns randomly generated data.
    """

    __slots__ = (
        "_data_fetch_process",
        "_data_generator",
        "_data_queue",
        "_running",
    )

    def __init__(self):
        """
        Initializes the object that pretends to be an IMU for testing purposes by returning
        randomly generated data.
        """
        # This limits the queue size to a very high limit, because the data generator will
        # generate all of the data before the imu reads it
        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue(
            MAX_QUEUE_SIZE
        )

        # Starts the process that fetches the generated data
        self._data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop,
            name="Sim IMU Process",
        )

        # Makes a boolean value that is shared between processes
        self._running = multiprocessing.Value("b", False)

        self._data_generator = DataGenerator()

    def _fetch_data_loop(self) -> None:
        """A wrapper function to suppress KeyboardInterrupt exceptions when obtaining generated
        data."""
        # unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            for i in range(2000):
                packets = self._data_generator.generate_data_packet()
                timestamp = 0
                if packets[0] is not None:
                    self._data_queue.put(packets[0])
                    timestamp = packets[0].timestamp / 1e9
                if packets[1] is not None:
                    self._data_queue.put(packets[1])
                    timestamp = packets[1].timestamp / 1e9

                dt = self._data_generator.update_timestamp(timestamp) - timestamp
                time.sleep(dt)
