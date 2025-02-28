"""Module for describing the data packet for the processed IMU data."""

import msgspec
import numpy as np


class ProcessorDataPacket(msgspec.Struct):
    """
    Represents a packet of processed data from the IMUDataProcessor. All of these fields are the
    processed values of the IMU's estimated data.
    """

    # When airbrakes are retracted, the current altitude is the pressure altitude. When deployed,
    # the current altitude is calculated by integrating the vertical velocity.
    current_altitude: np.float64
    pressure_altitude: np.float64  # This is the zeroed-out pressure altitude of the rocket.
    # This is the velocity of the rocket, in the upward axis (whichever way is up)
    vertical_velocity: np.float64
    # Velocity of the rocket calculated from differentiating the pressure altitude
    velocity_from_altitude: np.float64
    # Velocity of the rocket by filtering together integrated velocity and differentiated velocity
    filtered_velocity: np.float64
    # This is the acceleration of the rocket in the upwards direction.
    vertical_acceleration: np.float64
    # The time difference between the current and previous data packet.
    time_since_last_data_packet: np.float64
