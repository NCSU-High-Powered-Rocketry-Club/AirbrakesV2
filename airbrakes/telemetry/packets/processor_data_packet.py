"""Module for describing the data packet for the processed IMU data."""

import msgspec


class ProcessorDataPacket(msgspec.Struct, array_like=True, tag=True):
    """
    Represents a packet of processed data from the IMUDataProcessor. All of these fields are the
    processed values of the IMU's estimated data.
    """

    current_altitude: float  # This is the zeroed-out altitude of the rocket.
    # This is the velocity of the rocket, in the upward axis (whichever way is up)
    vertical_velocity: float
    # This is the acceleration of the rocket in the upwards direction.
    vertical_acceleration: float
    # The time difference between the current and previous data packet.
    time_since_last_data_packet: float
