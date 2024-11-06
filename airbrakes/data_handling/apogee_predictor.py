"""Module for predicting apogee"""

import multiprocessing
import signal
from collections import deque
from typing import Literal

import numpy as np
import numpy.typing as npt
from scipy.optimize import curve_fit

from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import (
    APOGEE_PREDICTION_FREQUENCY,
    CURVE_FIT_INITIAL,
    FLIGHT_LENGTH_SECONDS,
    GRAVITY,
    INTEGRATION_TIME_STEP,
    MIN_PREDICTION_TIME,
    STOP_SIGNAL,
    UNCERTAINTY_THRESHOLD,
)


class ApogeePredictor:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight, will
    be used to determine servo extension. Will use multiprocessing in the future.
    """

    __slots__ = (
        "_accelerations",
        "_apogee_prediction_value",
        "_cumulative_time_differences",
        "_current_altitude",
        "_current_velocity",
        "_has_apogee_converged",
        "_initial_velocity",
        "_predicted_apogees",
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
        self._has_apogee_converged: bool = False
        self._predicted_apogees: npt.NDArray[np.float64] = np.array([])
        self._initial_velocity = None

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

    @staticmethod
    def _curve_fit_function(t: float, a: float, b: float) -> float:
        """
        This function is only used internally by scipy curve_fit function
        Defines the function that the curve fit will use
        """
        return a * (1 - b * t) ** 4

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

    def _curve_fit(self) -> npt.NDArray[np.float64]:
        """
        Calculates the curve fit function of rotated compensated acceleration
        Uses the function y = A(1-Bt)^4, where A and B are parameters being fit
        :return: numpy array with values of A and B
        """
        # curve fit that returns popt: list of fitted parameters, and pcov: list of uncertainties
        popt, pcov = curve_fit(
            self._curve_fit_function,
            self._cumulative_time_differences,
            self._accelerations,
            p0=CURVE_FIT_INITIAL,
            maxfev=2000,
        )
        uncertainties = np.sqrt(np.diag(pcov))
        # determines the minimum amount of data points before we can declare apogee converged or not
        min_length = np.ceil(MIN_PREDICTION_TIME * APOGEE_PREDICTION_FREQUENCY)
        if np.all(
            (uncertainties < UNCERTAINTY_THRESHOLD) &
            (len(self._cumulative_time_differences) >= min_length)
            ):
            self._has_apogee_converged = True

        a, b = popt
        return np.array([a, b])

    def _create_prediction_lookup_table(
        self, curve_coefficients: npt.NDArray[np.float64]
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Curve fits the acceleration data and uses the curve fit to make a lookup table of velocity
        vs Δheight.
        :param: curve_coefficients: A length 2 array, containing the A and B values from curve fit
        function.
        :return: predicted altitude at apogee
        """

        # We need to store the velocity for when we start the prediction, so we can use it to
        # as the plus C in the integration of the acceleration function
        if self._initial_velocity is None:
            self._initial_velocity = self._current_velocity

        # To calculate the predicted apogee, we are integrating the acceleration function. The most
        # straightforward way to do this is to use the function with fitted parameters for A and B,
        # and a large incremental vector, with small uniform steps for the dependent variable of
        # the function, t. Then we can evaluate the function at every point in t, and use
        # cumulative sum to integrate for velocity, and repeat with velocity to integrate for
        # altitude.

        # This is all the x values that we will use to integrate the acceleration function
        predicted_coast_timestamps = np.arange(0, FLIGHT_LENGTH_SECONDS, INTEGRATION_TIME_STEP)

        # Makes sure that the curve coefficients are not None, sets them to the guessed initial
        # values if they are
        curve_coefficients = (
            curve_coefficients if curve_coefficients is not None else CURVE_FIT_INITIAL
        )

        predicted_accelerations = (
            curve_coefficients[0] * (1 - curve_coefficients[1] * predicted_coast_timestamps) ** 4
        ) - GRAVITY
        predicted_velocities = (
            np.cumsum(predicted_accelerations) * INTEGRATION_TIME_STEP + self._initial_velocity
        )
        # We don't care about velocity values less than 0 as those correspond with the rocket
        # falling
        predicted_velocities = predicted_velocities[predicted_velocities >= 0]
        predicted_altitudes = np.cumsum(predicted_velocities) * INTEGRATION_TIME_STEP
        predicted_apogee = np.max(predicted_altitudes)
        # We need to flip the lookup table because the velocities are in descending order, not
        # ascending order
        return np.flip(predicted_velocities), np.flip(predicted_apogee - predicted_altitudes)

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
                self._cumulative_time_differences = np.cumsum(self._time_differences)
                if not self._has_apogee_converged:
                    curve_coefficients = self._curve_fit()
                    lookup_table = self._create_prediction_lookup_table(curve_coefficients)
                else:
                    # Predicts the apogee using the lookup table and linear interpolation
                    # It gets the change in height from the lookup table, and adds it to the
                    # current height, thus giving you the predicted apogee.
                    predicted_apogee = (
                        np.interp(
                            self._current_velocity,
                            lookup_table[0],
                            lookup_table[1],
                        )
                        + self._current_altitude
                    )
                    self._apogee_prediction_value.value = predicted_apogee
                    self._predicted_apogees = np.append(self._predicted_apogees, predicted_apogee)
                last_run_length = len(self._accelerations)
