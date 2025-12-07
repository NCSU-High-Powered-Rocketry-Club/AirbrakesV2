"""
Module for predicting apogee.
"""

import queue
import threading
from collections import deque
from typing import TYPE_CHECKING, Literal

import msgspec
import msgspec.msgpack
import numpy as np
import numpy.typing as npt
from scipy.optimize import curve_fit

from airbrakes.constants import (
    APOGEE_PREDICTION_MIN_PACKETS,
    CURVE_FIT_INITIAL,
    FLIGHT_LENGTH_SECONDS,
    GRAVITY_METERS_PER_SECOND_SQUARED,
    INTEGRATION_TIME_STEP_SECONDS,
    STOP_SIGNAL,
    UNCERTAINTY_THRESHOLD,
)
from airbrakes.telemetry.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.utils import get_all_packets_from_queue

if TYPE_CHECKING:
    from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket

PREDICTED_COAST_TIMESTAMPS = np.arange(0, FLIGHT_LENGTH_SECONDS, INTEGRATION_TIME_STEP_SECONDS)


class LookupTable(msgspec.Struct):
    """
    The lookup table for the apogee predictor.

    This will store the respective velocities and delta heights for the lookup table. Updated every
    time the curve fit is run, until it converges.
    """

    velocities: npt.NDArray[np.float64] = np.array([0.0, 0.1])
    delta_heights: npt.NDArray[np.float64] = np.array([0.1, 0.1])


class CurveCoefficients(msgspec.Struct):
    """
    The curve coefficients for the apogee predictor.

    This will store the respective A and B values for the curve fit function.
    """

    A: np.float64 = np.float64(0.0)
    B: np.float64 = np.float64(0.0)
    uncertainties: npt.NDArray[np.float64] = np.array([0.0, 0.0])


class ApogeePredictor:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight.
    """

    __slots__ = (
        "_accelerations",
        "_apogee_predictor_packet_queue",
        "_cumulative_time_differences",
        "_current_altitude",
        "_current_velocity",
        "_has_apogee_converged",
        "_initial_velocity",
        "_prediction_thread",
        "_processor_data_packet_queue",
        "_time_differences",
        "lookup_table",
    )

    def __init__(self):
        # ------ Variables which can referenced in the main thread ------
        self._processor_data_packet_queue: queue.SimpleQueue[
            ProcessorDataPacket | Literal["STOP"]
        ] = queue.SimpleQueue()
        self._apogee_predictor_packet_queue: queue.SimpleQueue[ApogeePredictorDataPacket] = (
            queue.SimpleQueue()
        )

        self._prediction_thread = threading.Thread(
            target=self._prediction_loop, name="Apogee Prediction Thread"
        )

        self._cumulative_time_differences: npt.NDArray[np.float64] = np.array([])
        # list of all the accelerations since motor burn out:
        self._accelerations: deque[np.float64] = deque()
        # list of all the dt's since motor burn out
        self._time_differences: deque[np.float64] = deque()
        self._current_altitude: np.float64 = np.float64(0.0)
        self._current_velocity: np.float64 = np.float64(0.0)  # Velocity in the upwards axis
        self._has_apogee_converged: bool = False
        self._initial_velocity = None
        self.lookup_table: LookupTable = LookupTable()

    @property
    def is_running(self) -> bool:
        """
        Returns whether the prediction thread is running.

        :return: True if the thread is running, False otherwise.
        """
        return self._prediction_thread.is_alive()

    @property
    def processor_data_packet_queue_size(self) -> int:
        """
        Gets the number of data packets in the processor data packet queue.

        :return: The number of ProcessorDataPacket in the processor data packet queue.
        """
        return self._processor_data_packet_queue.qsize()

    def start(self) -> None:
        """
        Starts the prediction thread.

        This is called before the main loop starts.
        """
        self._prediction_thread.start()

    def stop(self) -> None:
        """
        Stops the prediction thread.
        """
        # Request the thread to stop:
        self._processor_data_packet_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        self._prediction_thread.join()

    def update(self, processor_data_packets: list[ProcessorDataPacket]) -> None:
        """
        Updates the apogee predictor to include the most recent processor data packets.

        This method should only be called during the coast phase of the rocket's flight.
        :param processor_data_packets: A list of ProcessorDataPacket objects to add to the queue.
        """
        for processor_data_packet in processor_data_packets:
            self._processor_data_packet_queue.put(processor_data_packet)

    def get_prediction_data_packets(self) -> list[ApogeePredictorDataPacket]:
        """
        Gets *all* of the apogee prediction data packets from the queue.

        This operation is non-blocking.
        :return: A list containing the latest IMU data packets from the packet queue.
        """
        total_packets = []
        new_packets = get_all_packets_from_queue(self._apogee_predictor_packet_queue, block=False)
        total_packets.extend(new_packets)
        return total_packets

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE THREAD -------------------------
    @staticmethod
    def _curve_fit_function(
        t: npt.NDArray[np.float64], a: np.float64, b: np.float64
    ) -> npt.NDArray:
        """
        The function which we fit the acceleration data to.

        Used by scipy.optimize.curve_fit and while creating the lookup table.
        """
        return a * (1 - b * t) ** 4

    def _curve_fit(self) -> CurveCoefficients:
        """
        Calculates the curve fit function of vertical direction of the acceleration.

        Uses the function y = A(1-Bt)^4, where A and B are parameters being fit.
        :return: The CurveCoefficients class, containing the A and B values from curve fit function
        """
        # curve fit that returns popt: list of fitted parameters, and pcov: list of uncertainties
        popt, pcov = curve_fit(
            self._curve_fit_function,
            self._cumulative_time_differences,
            self._accelerations,
            p0=CURVE_FIT_INITIAL,
            maxfev=2000,  # Maximum number of iterations
        )
        # Calculate the uncertainties of the curve fit, which is just the standard deviation of the
        # covariance matrix, which are the "errors" in the curve fit.
        uncertainties = np.sqrt(np.diag(pcov))
        if np.all(uncertainties < UNCERTAINTY_THRESHOLD):
            self._has_apogee_converged = True

        a, b = popt
        return CurveCoefficients(A=a, B=b, uncertainties=uncertainties)

    def _update_prediction_lookup_table(self, curve_coefficients: CurveCoefficients):
        """
        Curve fits the acceleration data and uses the curve fit to make a lookup table of velocity
        vs Δheight.

        :param: curve_coefficients: The CurveCoefficients class, containing the A and B values from
            curve fit function.
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
        predicted_accelerations = (
            self._curve_fit_function(
                PREDICTED_COAST_TIMESTAMPS, curve_coefficients.A, curve_coefficients.B
            )
            - GRAVITY_METERS_PER_SECOND_SQUARED
        )
        predicted_velocities = (
            np.cumsum(predicted_accelerations) * INTEGRATION_TIME_STEP_SECONDS
            + self._initial_velocity
        )
        # We don't care about velocity values less than 0 as those correspond with the rocket
        # falling
        predicted_velocities = predicted_velocities[predicted_velocities >= 0]
        predicted_altitudes = np.cumsum(predicted_velocities) * INTEGRATION_TIME_STEP_SECONDS
        predicted_apogee = np.max(predicted_altitudes)
        # We need to flip the lookup table because the velocities are in descending order, not
        # ascending order. We need them to be in ascending order for the interpolation to work.
        self.lookup_table.velocities = np.flip(predicted_velocities)
        self.lookup_table.delta_heights = np.flip(predicted_apogee - predicted_altitudes)

    def _prediction_loop(self) -> None:
        """
        Responsible for fetching data packets, curve fitting, updating our lookup table, and finally
        predicting the apogee.

        Runs in a separate thread.
        """
        last_run_length = 0

        # Makes placeholder values for the curve coefficients and apogee
        curve_coefficients = CurveCoefficients()
        apogee = 0.0

        # Keep checking for new data packets until the stop signal is received:
        while True:
            # Rather than having the queue store all the data packets, it is only used to
            # communicate between the main thread and the prediction thread. The main thread
            # will add the data packets to the queue, and the prediction thread will get the data
            # packets from the queue and add them to its own arrays.
            processor_data_packets = []

            processor_data_packets.extend(
                get_all_packets_from_queue(self._processor_data_packet_queue, block=True)
            )

            if STOP_SIGNAL in processor_data_packets:
                break

            self._extract_processor_data_packets(processor_data_packets)
            if len(self._accelerations) - last_run_length >= APOGEE_PREDICTION_MIN_PACKETS:
                self._cumulative_time_differences = np.cumsum(self._time_differences)

                # We only want to keep curve fitting if the curve fit hasn't converged yet
                if not self._has_apogee_converged:
                    curve_coefficients = self._curve_fit()
                    self._update_prediction_lookup_table(curve_coefficients)

                # Get the predicted apogee if the curve fit has converged:
                if self._has_apogee_converged:
                    apogee = self._predict_apogee()

                last_run_length = len(self._accelerations)

                # Send the apogee prediction to the main process
                self._apogee_predictor_packet_queue.put(
                    ApogeePredictorDataPacket(
                        predicted_apogee=apogee,
                        a_coefficient=curve_coefficients.A,
                        b_coefficient=curve_coefficients.B,
                        uncertainty_threshold_1=curve_coefficients.uncertainties[0],
                        uncertainty_threshold_2=curve_coefficients.uncertainties[1],
                    )
                )

    def _extract_processor_data_packets(self, data_packets: list[ProcessorDataPacket]) -> None:
        """
        Extracts the processor data packets from the data packets and appends them to the respective
        internal lists.

        :param data_packets: a list of ProcessorDataPackets to extract.
        """
        for data_packet in data_packets:
            self._accelerations.append(data_packet.vertical_acceleration)
            self._time_differences.append(data_packet.time_since_last_data_packet)

        self._current_altitude = data_packets[-1].current_altitude
        self._current_velocity = data_packets[-1].vertical_velocity

    def _predict_apogee(self) -> np.float64:
        """
        Predicts the apogee using the lookup table and linear interpolation.

        It gets the change in height from the lookup table, and adds it to the current height, thus
        giving you the predicted apogee.
        :return: the predicted apogee as a float.
        """
        return (
            np.interp(
                self._current_velocity,
                self.lookup_table.velocities,
                self.lookup_table.delta_heights,
            )
            + self._current_altitude
        )
