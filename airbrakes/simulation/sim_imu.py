"""Module for simulating the IMU on the rocket using generated data."""

import contextlib
import multiprocessing
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import yaml

if TYPE_CHECKING:
    from airbrakes.data_handling.imu_data_packet import IMUDataPacket

from airbrakes.hardware.imu import IMU
from airbrakes.simulation.data_generator import DataGenerator
from constants import MAX_QUEUE_SIZE


class SimIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns randomly generated data.
    """

    __slots__ = (
        "_config",
        "_data_fetch_process",
        "_data_generator",
        "_data_queue",
        "_running",
        "_timestamp",
    )

    def __init__(self) -> None:
        """
        Initializes the object that pretends to be an IMU for testing purposes by returning
        randomly generated data.
        """
        self._timestamp: np.float64 = np.float64(0.0)
        # loads the sim_config.yaml file
        config_path = Path("simulation/sim_config.yaml")
        with config_path.open(mode="r", newline="") as file:
            self._config: dict = yaml.safe_load(file)

        # This limits the queue size to a very high limit, because the data generator will
        # generate all the data before the imu reads it
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

    def update_timestamp(self, current_timestamp: np.float64) -> np.float64:
        """
        Updates the current timestamp of the data generator, based off time step defined in config.
        Will also determine if the next timestamp will be a raw packet, estimated packet, or both.
        :param current_timestamp: the current timestamp of the simulation
        :return: the updated current timestamp, rounded to 3 decimals
        """

        # finding whether the raw or estimated data packets have a lower time_step
        lowest_dt = min(self._config["raw_time_step"], self._config["est_time_step"])
        highest_dt = max(self._config["raw_time_step"], self._config["est_time_step"])

        # checks if current time is a multiple of the highest and/or lowest time step
        at_low = any(np.isclose(current_timestamp % lowest_dt, [0, lowest_dt]))
        at_high = any(np.isclose(current_timestamp % highest_dt, [0, highest_dt]))

        # If current timestamp is a multiple of both, the next timestamp will be the
        # current timestamp + the lower time steps
        if all([at_low, at_high]):
            return np.round(current_timestamp + lowest_dt, 3)

        # If timestamp is a multiple of just the lowest time step, the next will be
        # either current + lowest, or the next timestamp that is divisible by the highest
        if at_low and not at_high:
            dt = min(lowest_dt, highest_dt - (current_timestamp % highest_dt))
            return np.round(current_timestamp + dt, 3)

        # If timestamp is a multiple of only the highest time step, the next will
        # always be the next timestamp that is divisible by the lowest
        if at_high and not at_low:
            return np.round(current_timestamp + lowest_dt - (current_timestamp % lowest_dt), 3)

        # This would happen if the input current timestamp is not a multiple of the raw
        # or estimated time steps, or if there is a rounding/floating point error.
        raise ValueError("Could not update timestamp, time stamp is invalid")

    def _fetch_data_loop(self) -> None:
        """A wrapper function to suppress KeyboardInterrupt exceptions when obtaining generated
        data."""

        raw_dt = self._config["raw_time_step"]
        est_dt = self._config["est_time_step"]

        # unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            while self._data_generator.velocity > -1:
                # starts timer
                start_time = time.time()

                # if the timestamp is a multiple of the raw time step, generate a raw data packet.
                if any(np.isclose(self._timestamp % raw_dt, [0, raw_dt])):
                    self._data_queue.put(self._data_generator.generate_raw_data_packet())

                # if the timestamp is a multiple of the est time step, generate an est data packet.
                if any(np.isclose(self._timestamp % est_dt, [0, est_dt])):
                    self._data_queue.put(self._data_generator.generate_estimated_data_packet())

                # updates the timestamp and sleeps until next packet is ready in real-time
                time_step = self.update_timestamp(self._timestamp) - self._timestamp
                self._timestamp += time_step
                end_time = time.time()
                time.sleep(max(0.0, time_step - (end_time - start_time)))
