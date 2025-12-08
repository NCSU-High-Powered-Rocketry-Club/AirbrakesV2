"""
Module for simulating the IMU on the rocket using generated data.
"""

import contextlib
import queue
import threading
import time
from typing import TYPE_CHECKING

import numpy as np

from airbrakes.simulation.sim_config import SimulationConfig, get_configuration
from airbrakes.simulation.sim_utils import update_timestamp

if TYPE_CHECKING:
    from airbrakes.telemetry.packets.imu_data_packet import IMUDataPacket

from airbrakes.constants import ServoExtension
from airbrakes.interfaces.base_imu import BaseIMU
from airbrakes.simulation.data_generator import DataGenerator


class SimIMU(BaseIMU):
    """
    A mock implementation of the IMU for testing purposes.

    It doesn't interact with any hardware and returns randomly generated data.
    """

    def __init__(self, sim_type: str, real_time_replay: bool) -> None:
        """
        Initializes the object that pretends to be an IMU for testing purposes by returning randomly
        generated data.

        :param sim_type: The type of simulation to run. This can be either "full-scale" or "sub-
            scale".
        """
        # Gets the configuration for the simulation
        config = get_configuration(sim_type)

        data_queue: queue.SimpleQueue[IMUDataPacket] = queue.SimpleQueue()

        # Starts the thread that fetches the generated data
        data_fetch_thread = threading.Thread(
            target=self._fetch_data_loop,
            name="Sim IMU Thread",
            args=(config, real_time_replay),
        )

        super().__init__(data_fetch_thread, data_queue)
        # Makes boolean values that are shared between processes
        self._running = threading.Event()
        self._airbrakes_extended = threading.Event()

    def set_airbrakes_status(self, servo_extension: ServoExtension) -> None:
        """
        Sets the value of the shared boolean that indicates whether the airbrakes are extended.

        :param servo_extension: The extension of the airbrakes servo.
        """
        # Sets the shared boolean to True if the servo extension is at max extension or max no buzz
        self._airbrakes_extended.value = servo_extension in (
            ServoExtension.MAX_EXTENSION,
            ServoExtension.MAX_NO_BUZZ,
        )

    def _fetch_data_loop(self, config: SimulationConfig, real_time_replay: bool) -> None:
        """
        A wrapper function to suppress KeyboardInterrupt exceptions when obtaining generated data.
        """
        data_generator = DataGenerator(config)
        timestamp: np.float64 = np.float64(0.0)

        raw_dt = config.raw_time_step
        est_dt = config.est_time_step

        # unfortunately, doing the signal handling isn't always reliable, so we need to wrap the
        # function in a context manager to suppress the KeyboardInterrupt
        with contextlib.suppress(KeyboardInterrupt):
            while data_generator.velocity_vector[2] > -100:
                # starts timer
                start_time = time.time()

                data_generator.is_airbrakes_extended = self._airbrakes_extended.value

                # if the timestamp is a multiple of the raw time step, generate a raw data packet.
                if any(np.isclose(timestamp % raw_dt, [0, raw_dt])):  # ty: ignore[invalid-argument-type]
                    self._queued_imu_packets.put(data_generator.generate_raw_data_packet())

                # if the timestamp is a multiple of the est time step, generate an est data packet.
                if any(np.isclose(timestamp % est_dt, [0, est_dt])):  # ty: ignore[invalid-argument-type]
                    self._queued_imu_packets.put(data_generator.generate_estimated_data_packet())

                # updates the timestamp and sleeps until next packet is ready in real-time
                time_step = update_timestamp(timestamp, config) - timestamp
                timestamp += time_step
                end_time = time.time()

                if real_time_replay:
                    time.sleep(max(0.0, time_step - (end_time - start_time)))
