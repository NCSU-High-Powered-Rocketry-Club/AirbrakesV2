"""Module for predicting apogee"""

import numpy as np

from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.state import State
class ApogeePrediction:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight, will be used to determine
    servo extension. Will use multiprocessing in the future.

    :param: state: airbrakes state class
    :param: data_processor: IMUDataProcessor class
    :param: data_points: EstimatedDataPacket class
    """
    def __init__(self, state: State, data_processor: IMUDataProcessor, data_points: EstimatedDataPacket):
        self.state = state # not being used currently
        self.data_processor = data_processor
        self.data_points = data_points
        self._last_data_point = self.data_processor._last_data_point
        self._previous_velocity: float = 0.0

        self.GRAVITY = 9.798 # will use gravity vector in future

    def _calculate_speeds(self):
        """
        Calculates the velocity in the z direction using rotated acceleration values

        :return: current velocity in the z direction
        """
        rotated_accel = self.data_processor._rotated_accel

        # should just give 1 float I hope?
        time_diff = np.diff(data_point.timestamp for data_point in [self._last_data_point, self.data_points[-1]]) * 1e-9

        # adds gravity to the z component of rotated acceleration and multiplies by dt
        velocity = self._previous_velocity + (rotated_accel[2]+self.GRAVITY)*time_diff

        # updates previous velocity with new velocity
        self._previous_velocity = velocity

        return velocity
