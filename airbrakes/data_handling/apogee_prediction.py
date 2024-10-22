"""Module for predicting apogee"""

import multiprocessing
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import curve_fit

if TYPE_CHECKING:
    from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.state import CoastState, MotorBurnState, State

# TODO: See why this warning is being thrown for curve_fit:
warnings.filterwarnings("ignore", message="Covariance of the parameters could not be estimated")


class ApogeePredictor:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight, will be used to determine
    servo extension. Will use multiprocessing in the future.

    :param: state: airbrakes state class
    :param: data_processor: IMUDataProcessor class
    :param: data_points: A sequence of EstimatedDataPacket objects to process.
    """

    __slots__ = (
        "_accel",
        "_all_accel",
        "_all_time",
        "_apogee_prediction",
        "_context",
        "_data_points",
        "_gravity",
        "_last_data_point",
        "_params",
        "_previous_velocity",
        "_speed",
        "_start_time",
        "data_processor",
        "state",
        "_time_diff",
    )

    def __init__(self, state: State, data_processor: IMUDataProcessor, context: "AirbrakesContext"):
        self.data_processor = data_processor
        self._data_points = None
        self.state = state
        self._previous_velocity: float = 0.0
        self._all_accel: npt.NDArray[np.float64] = np.array([])
        self._all_time: npt.NDArray[np.float64] = np.array([])
        self._start_time: np.float64 | None = None
        self._apogee_prediction: np.float64 | None = np.float64(0.0)
        self._context = context
        self._last_data_point: EstimatedDataPacket | None = None
        self._time_diff: npt.NDArray[np.float64] | None = None

        self._gravity = 9.798  # will use gravity vector in future
        # self._data_points = multiprocessing.Queue(maxsize=100)

    @property
    def apogee(self) -> float:
        """
        Returns the predicted apogee of the rocket
        :return: predicted apogee as a float.
        """
        return float(self._apogee_prediction)

    # def start(self) -> None:
    #     """
    #     Starts the apogee prediction process. This is called before the main while loop starts.
    #     """
    #     self._log_process.start()

    def update(self, data_points: Sequence[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. Will recompute all of the necesary
        information, and recompute the apogee prediction
        :param data_points: A sequence of EstimatedDataPacket objects to process
        """

        # If the data points are empty, we don't want to try to process anything
        if not data_points:
            return

        self._data_points = data_points

        if self._last_data_point is None:
            # setting last data point as the first element, makes it so that the time diff
            # automatically becomes 0, and the speed becomes 0
            self._last_data_point = self._data_points[0]

        self._accel = self.data_processor._rotated_accel[2]
        self._speed = self._calculate_speeds(self._accel)

        # once in motor burn phase, gets timestamp so all future data used in curve fit has the start at t=0
        if self._all_time.size == 0 and isinstance(self.state, MotorBurnState) and self._start_time is None:
            self._start_time = self._data_points[-1].timestamp

        # not recording apogee prediction until coast phase
        self.state = self._context.state
        if isinstance(self.state, CoastState):
            self._params = self._curve_fit(self._accel)
            self._apogee_prediction = self._get_apogee(self._params, self._speed, self.data_processor.current_altitude)
        self._last_data_point = data_points[-1]

    def _calculate_speeds(self, rotated_accel: np.float64):
        """
        Calculates the velocity in the z direction using rotated acceleration values

        :param: rotated_accel: z direction of compensated acceleration after rotated to Earth frame of reference

        :return: current velocity in the z direction
        """

        # Get the time differences between each data point and the previous data point
        time_diffs = self._get_time_differences()
        
        # update previous_velocity
        previous_velocity = self._previous_velocity

        # adds gravity to the z component of rotated acceleration and multiplies by dt
        velocities: np.array = previous_velocity + np.cumsum(((rotated_accel * -1) - self._gravity) * time_diffs)
        
        # updates previous velocity with new velocity
        self._previous_velocity = velocities[-1]

        # only return last velocity in list
        return velocities[-1]

    def _get_time_differences(self) -> npt.NDArray[np.float64]:
        """
        Calculates the time difference between each data point and the previous data point. This cannot
        be called on the first update as _last_data_point is None.
        :return: A numpy array of the time difference between each data point and the previous data point.
        """
        # calculate the time differences between each data point
        # We are converting from ns to s, since we don't want to have a speed in m/ns^2
        # We are using the last data point to calculate the time difference between the last data point from the
        # previous loop, and the first data point from the current loop
        if self._time_diff is None:
            self._time_diff = np.diff([data_point.timestamp for data_point in [self._last_data_point, *self._data_points]]) * 1e-9
        return self._time_diff
    
    def get_time_differences(self) -> npt.NDArray[np.float64]:
        """Returns the time difference of the data points."""
        return self._time_diff

    def reset_time_diff(self):
        """Resets the time difference once update() is called."""
        self._time_diff = None

    def _curve_fit_function(self, t, a, b):
        """
        This function is only used internally by scipy curve_fit function
        Defines the function that the curve fit will use
        """
        return a * (1 - b * t) ** 4

    def _curve_fit(self, accel: np.float64):
        """
        Calculates the curve fit function of rotated compensated acceleration
        Uses the function y = A(1-Bt)^4, where A and B are parameters being fit

        :param: accel: rotated compensated acceleration

        :return: numpy array with values of A and B
        """

        # creates running list of rotated acceleration, and associated timestamp
        self._all_time = np.append(self._all_time, (self._data_points[-1].timestamp - self._start_time) * 1e-9)
        self._all_accel = np.append(self._all_accel, accel)
        # initial values for curve fit
        CURVE_FIT_INITIAL = [15.5, 0.03]

        if len(self._all_accel) and len(self._all_time) >= 30:
            # curve fit that returns popt: list of fitted parameters, and pcov: list of uncertainties
            popt, _pcov = curve_fit(self._curve_fit_function, self._all_time, self._all_accel, p0=CURVE_FIT_INITIAL,maxfev = 2000)
            a, b = popt
            return np.array([a, b])
        return None

    def _get_apogee(self, params, velocity, altitude):
        """
        Uses curve fit and current velocity and altitude to predict the apogee

        :param: params: A and B values from curve fit function
        :param: velocity: current upwards velocity, after rotation is applied
        :param: altitude: current estimated pressure altitude

        :return: predicted altitude at apogee
        """
        # average time diff between estimated data packets
        dts = self._get_time_differences()
        avg_dt = sum(dts)/len(dts)

        # to calculate the predicted apogee, we are integrating the acceleration function. The most
        # straightfoward way to do this is to use the function with fitted parameters for A and B, and
        # a large incremental vector, with small uniform steps for the dependent variable of the function, t.
        # Then we can evaluate the function at every point in t, and use cumulative trapezoids to integrate
        # for velocity, and repeat with velocity to integrate for altitude.

        # arbitrary vector that just simulates a time from 0 to 30 seconds
        xvec = np.arange(0, 30.02, avg_dt)

        # uses the timestamp of the current data point and the timestamp of when the rocket leaves the launch pad
        # to determine what point in xvec the current time lines up with.
        current_vec_point = np.int64(np.floor(((self._data_points[-1].timestamp - self._start_time) * 1e-9) / avg_dt))

        if params is None:
            return 0.0

        estAccel = -self._gravity - (params[0] * (1 - params[1] * xvec) ** 4)
        estVel = cumulative_trapezoid(estAccel[current_vec_point:-1]) * avg_dt + velocity
        estAlt = cumulative_trapezoid(estVel) * avg_dt + altitude
        return np.max(estAlt)
