"""Module for predicting apogee"""

import multiprocessing
import signal
import warnings
from collections import deque
from multiprocessing import Event
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.optimize import curve_fit

from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import (
    APOGEE_PREDICTION_FREQUENCY,
    CONVERGENCE_THRESHOLD,
    CURVE_FIT_INITIAL,
    GRAVITY,
    NUMBER_OF_PREDICTIONS,
    STOP_SIGNAL,
)

# TODO: See why this warning is being thrown for curve_fit:
warnings.filterwarnings("ignore", message="Covariance of the parameters could not be estimated")


class ApogeePredictor:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight, will
    be used to determine servo extension. Will use multiprocessing in the future.

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
        "_predicted_apogees",
        "_prediction_complete",
        "_prediction_process",
        "_prediction_queue",
        "_time_differences",
    )

    def __init__(self):
        self._apogee_prediction_value = multiprocessing.Value("d", 0.0)
        self._prediction_queue: multiprocessing.Queue[
            deque[ProcessedDataPacket] | Literal["STOP"]
        ] = multiprocessing.Queue()
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
        self._prediction_complete = Event()
        self._predicted_apogees: npt.NDArray[np.float64] = np.array([])

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
        # The .copy() below is critical to ensure the data is actually transferred correctly to
        # the apogee prediction process.
        self._prediction_queue.put(processed_data_packets.copy())

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

        :return: numpy array with values of A and B
        """
        # curve fit that returns popt: list of fitted parameters, and pcov: list of uncertainties
        popt = curve_fit(
            self._curve_fit_function,
            self._cumulative_time_differences,
            self._accelerations,
            p0=CURVE_FIT_INITIAL,
            maxfev=2000,
        )[0]
        a, b = popt
        return np.array([a, b])

    def _generate_prediction(
        self, curve_coefficients: npt.NDArray[np.float64]
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Curve fits the acceleration data and uses the curve fit to make a lookup table of velocity
        vs Δheight.
        :param: curve_coefficients: A length 2 array, containing the A and B values from curve fit
            function.
        :return: predicted altitude at apogee
        """
        # average time diff between estimated data packets
        avg_dt = np.mean(self._time_differences)

        # to calculate the predicted apogee, we are integrating the acceleration function. The most
        # straightfoward way to do this is to use the function with fitted parameters for A and B,
        # and a large incremental vector, with small uniform steps for the dependent variable of
        # the function, t. Then we can evaluate the function at every point in t, and use
        # cumsum to integrate for velocity, and repeat with velocity to integrate for altitude.

        # arbitrary vector that just simulates a time from 0 to 30 seconds
        xvec = np.arange(0, 30.02, avg_dt)
        # sums up the time differences to get a vector with all the timestamps of each data packet,
        # from the start of coast phase. This determines what point in xvec the current time lines
        # up with. This is used as the start of the integral and the 30 seconds at the end of xvec
        # is the end of the integral. The idea is to integrate the acceleration and velocity
        # functions during the time between the current time, and 30 seconds (well after apogee,
        # to be safe)
        current_vec_point = np.int64(np.floor(self._cumulative_time_differences[-1] / avg_dt))

        if curve_coefficients is None:
            return np.float64(0.0)

        predicted_accelerations = (
            curve_coefficients[0] * (1 - curve_coefficients[1] * xvec) ** 4
        ) - GRAVITY
        predicted_velocities = (
            np.cumsum(predicted_accelerations[current_vec_point:-1]) * avg_dt
            + self._current_velocity
        )
        predicted_altitudes = np.cumsum(predicted_velocities) * avg_dt + self._current_altitude

        predicted_apogee = np.max(predicted_altitudes)

        return predicted_velocities, predicted_apogee - predicted_altitudes

        # TODO: Do something about this problem:
        # if not predicted_altitudes.size:  # Sanity check - if our dt is too big, max() will fail
        #     return 0.0

    def _prediction_loop(self) -> None:
        """
        The loop that will run the prediction process. It runs in parallel with the main loop.
        """
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal
        last_run_length = 0

        # Initial lookup table, will be updated with the first prediction, these are just dummy
        # values that ensure no division by zero errors
        lookup_table: tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]] = (
            np.array([0.0, 0.1]),
            np.array([0.1, 0.1]),
        )

        # Keep checking for new data packets until the stop signal is received:
        while True:
            # Rather than having the queue store all the data packets, it is only used to
            # communicate between the main process and the prediction process. The main process
            # will add the data packets to the queue, and the prediction process will get the data
            # packets from the queue and add them to its own arrays.
            # TODO: make it so _prediction_queue is a queue of data packets, not a queue of lists
            # of data packets
            data_packets = self._prediction_queue.get()

            if data_packets == STOP_SIGNAL:
                break
            for data_packet in data_packets:
                self._accelerations.append(data_packet.vertical_acceleration)
                self._time_differences.append(data_packet.time_since_last_data_packet)
                self._current_altitude = data_packet.current_altitude
                self._current_velocity = data_packet.vertical_velocity

            if len(self._accelerations) - last_run_length >= APOGEE_PREDICTION_FREQUENCY:
                # We only want to keep curve fitting if the curve fit hasn't converged yet
                if not self._has_apogee_converged():
                    curve_coefficients = self._curve_fit()
                    lookup_table = self._generate_prediction(curve_coefficients)
                self._cumulative_time_differences = np.cumsum(self._time_differences)
                # Predicts the apogee using the lookup table and linear interpolation
                predicted_apogee = np.interp(
                    self._current_velocity, lookup_table[0], lookup_table[1]
                )
                self._apogee_prediction_value.value = predicted_apogee
                self._predicted_apogees = np.append(self._predicted_apogees, predicted_apogee)
                last_run_length = len(self._accelerations)
            # notifies tests that prediction is complete
            self._prediction_complete.set()

    def _has_apogee_converged(self) -> bool:
        """
        Checks if the last 5 apogees are within 3% of each other.
        :return: True if the last 5 apogees are within 3% of each other, otherwise False.
        """
        if len(self._predicted_apogees) < NUMBER_OF_PREDICTIONS:
            return False  # Not enough data to check convergence

        # Because we return 0.0 if apogee hasn't been predicted, we don't want to say it's
        # converged if there's any 0s
        if np.any(self._predicted_apogees == 0):
            return False

        avg_apogee = np.mean(self._predicted_apogees[-NUMBER_OF_PREDICTIONS:])

        # Check if each apogee is within 3% of the average
        return bool(
            np.abs(self._predicted_apogees[-1] - avg_apogee) / avg_apogee <= CONVERGENCE_THRESHOLD
        )
