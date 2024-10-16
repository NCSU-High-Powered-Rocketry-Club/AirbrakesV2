"""Module for predicting apogee"""

from collections.abc import Sequence
from scipy.optimize import curve_fit
from scipy.integrate import cumulative_trapezoid

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.state import State, CoastState


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
        "_accel",
        "_speed",
        "_all_accel",
        "_all_time",
        "_burnout_time",
        "_apogee_prediction",
    )

    def __init__(self, state: State, data_processor: IMUDataProcessor, data_points: Sequence[EstimatedDataPacket]):
        self.state = state
        self.data_processor = data_processor
        self.data_points = data_points
        self._previous_velocity: float = 0.0
        self._all_accel: npt.NDArray[np.float64] = np.array([])
        self._all_time: npt.NDArray[np.float64] = np.array([])
        self._burnout_time: np.float64 | None = None
        self._apogee_prediction: np.float64 | None = None

        self._gravity = 9.798 # will use gravity vector in future

    def update_data(self,data_points: Sequence[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. Will recompute all of the necesary
        information, and recompute the apogee prediction
        :param data_points: A sequence of EstimatedDataPacket objects to process
        """

        # If the data points are empty, we don't want to try to process anything
        if not data_points:
            return
        
        self._data_points = data_points

        self.state = self.state.context.state

        self._accel = self.data_processor._rotated_accel[2]

        self._speed = self._calculate_speeds(self._accel)

        # not recording apogee prediction until coast phase
        if isinstance(self.state, CoastState):
            params = self._curve_fit(self._accel)
            self._apogee_prediction = self._get_apogee(params,self._speed,self.data_processor.current_altitude)

        self._last_data_point = data_points[-1]


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
    
    def _curve_fit_function(self,t,a,b):
        """
        This function is only used internally by scipy curve_fit function
        Defines the function that the curve fit will use
        """
        return a*(1-b*t)**4
    
    def _curve_fit(self,accel : npt.NDArray[np.float64]):
        """
        Calculates the curve fit function of rotated compensated acceleration
        Uses the function y = A(1-Bt)^4, where A and B are parameters being fit

        :param: accel: rotated compensated acceleration

        :return: numpy array with values of A and B
        """

        # once in coast phase, gets timestamp so all future data used in curve fit has burnout at t=0
        if not self._all_time:
            self._burnout_time = self.data_points[-1].timestamp
        
        # creates running list of rotated acceleration, and associated timestamp
        self._all_time = np.append(self._all_time, (self.data_points[-1].timestamp-self._burnout_time)*1e-9)
        self._all_accel = np.append(self._all_accel,accel)

        # initial values for curve fit
        CURVE_FIT_INITIAL = [15.5, 0.03]

        # curve fit that returns popt: list of fitted parameters, and pcov: list of uncertainties
        popt,pcov = curve_fit(self._curve_fit_function,self._all_time,self._all_accel,p0=CURVE_FIT_INITIAL)
        a,b = popt
        return np.array([a,b])

    
    def _get_apogee(self, params, velocity, altitude):
        """
        Uses curve fit and current velocity and altitude to predict the apogee

        :param: params: A and B values from curve fit function
        :param: velocity: current upwards velocity, after rotation is applied
        :param: altitude: current estimated pressure altitude

        :return: predicted altitude at apogee
        """
        # time diff between estimated data packets
        # will use something better later
        DT = 0.002

        # arbitrary vector that just simulates a time from 0 to 30 seconds
        xvec = np.arange(0,30.02,0.002)

        estAccel = -self._gravity - (params[0] * (1 - params[1]*xvec)**4)
        estVel = cumulative_trapezoid(estAccel)*DT + velocity
        estAlt = cumulative_trapezoid(estVel)*DT + altitude
        return np.max(estAlt)
