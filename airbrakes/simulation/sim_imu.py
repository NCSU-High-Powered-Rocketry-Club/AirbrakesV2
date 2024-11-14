"""Module for simulating the IMU on the rocket using generated data."""

import contextlib
import multiprocessing
import time
from typing import TYPE_CHECKING

import numpy as np

from airbrakes.simulation.sim_config import SimulationConfig, get_configuration

if TYPE_CHECKING:
    from airbrakes.data_handling.imu_data_packet import IMUDataPacket

from airbrakes.hardware.imu import IMU
from airbrakes.simulation.data_generator import DataGenerator
from constants import MAX_QUEUE_SIZE, ServoExtension


class SimIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns randomly generated data.
    """

    def __init__(self, sim_type: str) -> None:
        """
        Initializes the object that pretends to be an IMU for testing purposes by returning
        randomly generated data.
        :param sim_type: The type of simulation to run. This can be either "full-scale" or
          "sub-scale".
        """
        # Gets the configuration for the simulation
        config = get_configuration(sim_type)

        # This limits the queue size to a very high limit
        # TODO: should be smaller limit
        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue(
            MAX_QUEUE_SIZE
        )

        # Starts the process that fetches the generated data
        self._data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop,
            name="Sim IMU Process",
            args=(config,),
        )

        # Makes boolean values that are shared between processes
        self._running = multiprocessing.Value("b", False)
        self._airbrakes_extended = multiprocessing.Value("b", False)

    @staticmethod
    def _update_timestamp(current_timestamp: np.float64, config: SimulationConfig) -> np.float64:
        """
        Updates the current timestamp of the data generator, based off time step defined in config.
        Will also determine if the next timestamp will be a raw packet, estimated packet, or both.
        :param current_timestamp: the current timestamp of the simulation
        :return: the updated current timestamp, rounded to 3 decimals
        """

        # finding whether the raw or estimated data packets have a lower time_step
        lowest_dt = min(config.raw_time_step, config.est_time_step)
        highest_dt = max(config.raw_time_step, config.est_time_step)

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

    def set_airbrakes_status(self, servo_extension: ServoExtension) -> None:
        """
        Sets the value of the shared boolean that indicates whether the airbrakes are extended.
        :param servo_extension: The extension of the airbrakes servo.
        """
        # Sets the shared boolean to True if the servo extension is at max extension or max no buzz
        self._airbrakes_extended.value = (
            servo_extension in (ServoExtension.MAX_EXTENSION, ServoExtension.MAX_NO_BUZZ)
        )

    def _fetch_data_loop(self, config: SimulationConfig) -> None:
        """A wrapper function to suppress KeyboardInterrupt exceptions when obtaining generated
        data."""

        data_generator = DataGenerator(config)
        timestamp: np.float64 = np.float64(0.0)

        raw_dt = config.raw_time_step
        est_dt = config.est_time_step

        # unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            while data_generator.velocities[2] > -100:
                # starts timer
                start_time = time.time()

                data_generator.is_airbrakes_extended = self._airbrakes_extended.value

                # if the timestamp is a multiple of the raw time step, generate a raw data packet.
                if any(np.isclose(timestamp % raw_dt, [0, raw_dt])):
                    self._data_queue.put(data_generator.generate_raw_data_packet())

                # if the timestamp is a multiple of the est time step, generate an est data packet.
                if any(np.isclose(timestamp % est_dt, [0, est_dt])):
                    self._data_queue.put(data_generator.generate_estimated_data_packet())

                # updates the timestamp and sleeps until next packet is ready in real-time
                time_step = self._update_timestamp(timestamp, config) - timestamp
                timestamp += time_step
                end_time = time.time()
                time.sleep(max(0.0, time_step - (end_time - start_time)))
                # if self._data_generator._last_est_packet.timestamp>1.02e9:
