"""Module for simulating the IMU on the rocket using generated data."""

from airbrakes.hardware.imu import IMU


class SimIMU(IMU):
    """
    A mock implementation of the IMU for testing purposes. It doesn't interact with any hardware
    and returns randomly generated data.
    """
    def __init__(self):
        """
        Initializes the object that pretends to be an IMU for testing purposes by returning
        randomly generated data.
        """
