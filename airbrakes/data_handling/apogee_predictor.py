"""Module for predicting apogee"""

import multiprocessing
import warnings
from collections import deque
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import signal
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import curve_fit

from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket

if TYPE_CHECKING:
    from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.state import CoastState, MotorBurnState, State
from constants import GRAVITY, CURVE_FIT_INITIAL

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
        "_apogee_prediction",
        "_apogee_prediction_value",
        "_gravity",
        "_params",
        "_prediction_process",
        "_prediction_queue",
        "_running",
        "_start_time",
    )

    def __init__(self):
        # self._start_time: np.float64 | None = None
        # create a pipe to transfer our predicted apogee to the main process.
        self._apogee_prediction_value = multiprocessing.Value("d", 0.0)
        self._apogee_prediction: np.float64 | None = np.float64(0.0)

        # TODO: decide on packet limit? Also how does it work? If we try to add 200 packets and the limit is 100,
        #  will it add the first 100 packets or the last 100 packets (we would want last 100--this could be a time save)
        self._running = multiprocessing.Value("b", False)  # Makes a boolean value that is shared between processes
        self._prediction_queue: multiprocessing.Queue[ProcessedDataPacket] = multiprocessing.Queue()
        self._prediction_process = multiprocessing.Process(
            target=self._prediction_loop, name="Apogee Prediction Process"
        )

    @property
    def apogee(self) -> float:
        """
        Returns the predicted apogee of the rocket
        :return: predicted apogee as a float.
        """
        return float(self._apogee_prediction_value.value)

    @property
    def is_running(self) -> bool:
        """
        Returns whether the prediction process is running.
        """
        return self._running.value

    def start(self) -> None:
        """
        Starts the prediction process. This is called before the main while loop starts.
        """
        self._running.value = True
        self._prediction_process.start()

    def stop(self) -> None:
        """
        Stops the logging process. It will finish logging the current message and then stop.
        """
        if self._running.value:
            self._running.value = False
            # Waits for the process to finish before stopping it
            self._prediction_process.join()

    def update(self, processed_data_packets: deque[ProcessedDataPacket]) -> None:
        """
        Updates the apogee predictor to include the most recent processed data packets. This method
        should only be called during the coast phase of the rocket's flight.
        :param processed_data_packets: A list of ProcessedDataPacket objects to add to the queue.
        """
        self._prediction_queue.put(processed_data_packets)

    @staticmethod
    def _curve_fit_function(t, a, b):
        """
        This function is only used internally by scipy curve_fit function
        Defines the function that the curve fit will use
        """
        return a * (1 - b * t) ** 4

    @staticmethod
    def _curve_fit(accelerations: deque[float], cumulative_time_differences: deque[float]) -> npt.NDArray[np.float64]:
        """
        Calculates the curve fit function of rotated compensated acceleration
        Uses the function y = A(1-Bt)^4, where A and B are parameters being fit

        :param: accel: rotated compensated acceleration of the vertical axis
        :param: cumulative_time_differences: an array of the cumulative time differences. E.g. 0.002, 0.004, 0.006, etc

        :return: numpy array with values of A and B
        """
        # mean = np.mean(cumulative_time_differences)
        # curve fit that returns popt: list of fitted parameters, and pcov: list of uncertainties
        # print(accelerations)
        popt, _ = curve_fit(
            ApogeePredictor._curve_fit_function,
            cumulative_time_differences,
            accelerations,
            p0=CURVE_FIT_INITIAL,
            maxfev=2000,
        )
        a, b = popt
        # print(f"{a=} {b=}")
        return np.array([a, b])

    @staticmethod
    def _get_apogee(params, current_velocity, altitude, time_differences):
        """
        Uses curve fit and current velocity and altitude to predict the apogee

        :param: params: A and B values from curve fit function
        :param: velocity: current upwards velocity, after rotation is applied
        :param: altitude: current estimated pressure altitude
        :param: time_differences: array of time differences between data packets

        :return: predicted altitude at apogee
        """
        # average time diff between estimated data packets
        # dts = self._get_time_differences()
        avg_dt = np.mean(time_differences)

        # to calculate the predicted apogee, we are integrating the acceleration function. The most
        # straightfoward way to do this is to use the function with fitted parameters for A and B, and
        # a large incremental vector, with small uniform steps for the dependent variable of the function, t.
        # Then we can evaluate the function at every point in t, and use cumulative trapezoids to integrate
        # for velocity, and repeat with velocity to integrate for altitude.

        # arbitrary vector that just simulates a time from 0 to 30 seconds
        xvec = np.arange(0, 30.02, avg_dt)
        cumalative_timestamps = np.cumsum(time_differences)
        # sums up the time differences to get a vector with all the timestamps of each data packet, from the start of coast
        # phase. This determines what point in xvec the current time lines up with. This is used as the start of the
        # integral and the 30 seconds at the end of xvec is the end of the integral. The idea is to integrate the acceleration
        # and velocity functions during the time between the current time, and 30 seconds (well after apogee, to be safe)
        current_vec_point = np.int64(np.floor(cumalative_timestamps[-1] / avg_dt))

        if params is None:
            return 0.0

        estAccel = -GRAVITY - (params[0] * (1 - params[1] * xvec) ** 4)
        estVel = np.cumsum(estAccel[current_vec_point:-1]) * avg_dt + current_velocity
        estAlt = np.cumsum(estVel) * avg_dt + altitude
        return np.max(estAlt)

    def _prediction_loop(self):
        """
        The loop that will run the prediction process. It runs in parallel with the main loop.
        """
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal
        # These arrays belong to the prediction process, and are used to store the data packets that are passed in
        current_altitude: float = 0
        current_velocity: float = 0
        accelerations: deque[float] = []  # list of all the accelerations since motor burn out
        time_differences: deque[float] = []  # list of all the dt's since motor burn out
        last_run_length = 0
        # print("Prediction loop started!")

        while self._running.value:
            # Rather than having the queue store all the data packets, it is only used to communicate between the main
            # process and the prediction process. The main process will add the data packets to the queue, and the
            # prediction process will get the data packets from the queue and add them to its own arrays.
            data_packets = self._prediction_queue.get()
            for data_packet in data_packets:
                accelerations.append(data_packet.vertical_acceleration)
                time_differences.append(data_packet.time_since_last_data_point)
                current_altitude = data_packet.current_altitude
                current_velocity = data_packet.vertical_velocity

            # TODO: play around with this value
            if len(accelerations) > 100 and len(accelerations) - last_run_length > 100:
                curve_fit_timestamps = np.cumsum(time_differences)
                params = ApogeePredictor._curve_fit(accelerations, curve_fit_timestamps)
                self._apogee_prediction_value.value = ApogeePredictor._get_apogee(
                    params, current_velocity, current_altitude, time_differences
                )
                last_run_length = len(accelerations)
                print(f"The predicted apogee is: {self._apogee_prediction_value.value}")
