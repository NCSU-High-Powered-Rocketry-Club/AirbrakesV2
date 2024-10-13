"""Module for predicting apogee"""

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.state import State


class ApogeePrediction:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight, will be used to determine
    servo extension. Will use multiprocessing in the future.

    :param: state: airbrakes state class (currently unused)
    :param: data_processor: IMUDataProcessor class
    :param: data_points: EstimatedDataPacket class
    """

    __slots__ = (
        "state",
        "data_processor",
        "_previous_velocity",
        "_gravity",
        "data_points",
    )

    def __init__(self, state: State, data_processor: IMUDataProcessor, data_points: Sequence[EstimatedDataPacket]):
        self.state = state
        self.data_processor = data_processor
        self.data_points = data_points
        self._previous_velocity: float = 0.0

        self._gravity = 9.798 # will use gravity vector in future

    def _calculate_speeds(self, rotated_accel : npt.NDArray[np.float64]):
        """
        Calculates the velocity in the z direction using rotated acceleration values

        :param: rotated_accel: compensated acceleration after rotated to Earth frame of reference

        :return: current velocity in the z direction
        """
        last_data_point : EstimatedDataPacket = self.data_processor._last_data_point

        # gives dt between last data point of data_points (should be timestamp of rotated_accel?), and last_data_point
        time_diff = (self.data_points[0].timestamp - last_data_point.timestamp) * 1e-9

        # adds gravity to the z component of rotated acceleration and multiplies by dt
        velocity = self._previous_velocity + (rotated_accel[2]+self._gravity)*time_diff

        # updates previous velocity with new velocity
        self._previous_velocity = velocity

        return velocity
