"""Module for predicting apogee"""

import multiprocessing
import signal
import warnings
from collections import deque
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.optimize import curve_fit

from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import APOGEE_PREDICTION_FREQUENCY, CURVE_FIT_INITIAL, GRAVITY, STOP_SIGNAL

# TODO: See why this warning is being thrown for curve_fit:
warnings.filterwarnings("ignore", message="Covariance of the parameters could not be estimated")


class ApogeePredictor:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight, will be used to determine
    servo extension. Will use multiprocessing in the future.

    :param: state: airbrakes state class
    :param: data_processor: IMUDataProcessor class
    :param: data_packets: A sequence of EstimatedDataPacket objects to process.
    """

    __slots__ = (
        "_accelerations",
        "_apogee_prediction_value",
        "_cumulative_time_differences",
        "_current_altitude",
        "_current_velocity",
        "_prediction_process",
        "_prediction_queue",
        "_time_differences",
    )

    def __init__(self):
        self._apogee_prediction_value = multiprocessing.Value("d", 0.0)
        self._prediction_queue: multiprocessing.Queue[deque[ProcessedDataPacket] | Literal["STOP"]] = (
            multiprocessing.Queue()
        )
        self._prediction_process = multiprocessing.Process(
            target=self._prediction_loop, name="Apogee Prediction Process"
        )
        self._cumulative_time_differences: npt.NDArray[np.float64] = np.array([])
        # list of all the accelerations since motor burn out:
        self._accelerations: deque[np.float64] = deque()
        # list of all the dt's since motor burn out
        self._time_differences: deque[np.float64] = deque()
        self._current_altitude: np.float64 = np.float64(0.0)
        self._current_velocity: np.float64 = np.float64(0.0)  # Velocity in the vertical axis

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
        return self._prediction_process.is_alive()

    def start(self) -> None:
        """
        Starts the prediction process. This is called before the main while loop starts.
        """
        self._prediction_process.start()

    def stop(self) -> None:
        """
        Stops the prediction process.
        """
        # Waits for the process to finish before stopping it
        self._prediction_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        self._prediction_process.join()

    def update(self, processed_data_packets: deque[ProcessedDataPacket]) -> None:
        """
        Updates the apogee predictor to include the most recent processed data packets. This method
        should only be called during the coast phase of the rocket's flight.

        :param processed_data_packets: A list of ProcessedDataPacket objects to add to the queue.
        """
        self._prediction_queue.put(processed_data_packets)

    def _curve_fit_function(self, t, a, b):
        """
        This function is only used internally by scipy curve_fit function
        Defines the function that the curve fit will use
        """
        return a * (1 - b * t) ** 4

    def _curve_fit(self) -> npt.NDArray[np.float64]:
        """
        Calculates the curve fit function of rotated compensated acceleration
        Uses the function y = A(1-Bt)^4, where A and B are parameters being fit

        :param: accel: rotated compensated acceleration of the vertical axis
        :param: cumulative_time_differences: an array of the cumulative time differences. E.g. 0.002, 0.004, 0.006, etc

        :return: numpy array with values of A and B
        """
        # curve fit that returns popt: list of fitted parameters, and pcov: list of uncertainties
        popt, _ = curve_fit(
            self._curve_fit_function,
            self._cumulative_time_differences,
            self._accelerations,
            p0=CURVE_FIT_INITIAL,
            maxfev=2000,
        )
        a, b = popt
        return np.array([a, b])

    def _get_apogee(self, params: npt.NDArray[np.float64]) -> np.float64:
        """
        Uses curve fit and current velocity and altitude to predict the apogee

        :param: params: A length 2 array, containing the A and B values from curve fit function

        :return: predicted altitude at apogee
        """
        # average time diff between estimated data packets
        avg_dt = np.mean(self._time_differences)

        # to calculate the predicted apogee, we are integrating the acceleration function. The most
        # straightfoward way to do this is to use the function with fitted parameters for A and B, and
        # a large incremental vector, with small uniform steps for the dependent variable of the function, t.
        # Then we can evaluate the function at every point in t, and use cumulative trapezoids to integrate
        # for velocity, and repeat with velocity to integrate for altitude.

        # arbitrary vector that just simulates a time from 0 to 30 seconds
        xvec = np.arange(0, 30.02, avg_dt)
        # sums up the time differences to get a vector with all the timestamps of each data packet,
        # from the start of coast phase. This determines what point in xvec the current time lines
        # up with. This is used as the start of the integral and the 30 seconds at the end of xvec
        # is the end of the integral. The idea is to integrate the acceleration and velocity functions
        # during the time between the current time, and 30 seconds (well after apogee, to be safe)
        current_vec_point = np.int64(np.floor(self._cumulative_time_differences[-1] / avg_dt))

        if params is None:
            return 0.0

        est_accels = (params[0] * (1 - params[1] * xvec) ** 4) - GRAVITY
        est_velocities = np.cumsum(est_accels[current_vec_point:-1]) * avg_dt + self._current_velocity
        est_altitudes = np.cumsum(est_velocities) * avg_dt + self._current_altitude

        # TODO: Do something about this problem:
        # if not est_altitudes.size:  # Sanity check - if our dt is too big, est_alt will be empty, failing max()
        #     return 0.0

        return np.max(est_altitudes)

    def _prediction_loop(self) -> None:
        """
        The loop that will run the prediction process. It runs in parallel with the main loop.
        """
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal
        # These arrays belong to the prediction process, and are used to store the data packets that are passed in
        last_run_length = 0
        # Keep checking for new data packets until the stop signal is received:
        while True:
            # Rather than having the queue store all the data packets, it is only used to communicate between the main
            # process and the prediction process. The main process will add the data packets to the queue, and the
            # prediction process will get the data packets from the queue and add them to its own arrays.
            data_packets = self._prediction_queue.get()

            if data_packets == STOP_SIGNAL:
                break

            for data_packet in data_packets:
                self._accelerations.append(data_packet.vertical_acceleration)
                self._time_differences.append(data_packet.time_since_last_data_packet)
                self._current_altitude = data_packet.current_altitude
                self._current_velocity = data_packet.vertical_velocity

            # TODO: play around with this value
            # Run apogee prediction every 100 data points:
            if len(self._accelerations) - last_run_length >= APOGEE_PREDICTION_FREQUENCY:
                self._cumulative_time_differences = np.cumsum(self._time_differences)
                params = self._curve_fit()
                self._apogee_prediction_value.value = self._get_apogee(params)
                last_run_length = len(self._accelerations)
