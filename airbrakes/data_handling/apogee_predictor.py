"""Module for predicting apogee."""

import math
import queue
import threading
from typing import TYPE_CHECKING, Literal, cast

from hprm import InitialState3DOF, OdeMethod, Rocket

from airbrakes import constants
from airbrakes.constants import (
    STOP_SIGNAL,
)
from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
    ApogeePredictorDataPacket,
)
from airbrakes.utils import get_all_packets_from_queue

if TYPE_CHECKING:
    from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket


class ApogeePredictor:
    """
    Class that performs the calculations to predict the apogee of the rocket
    during flight.
    """

    __slots__ = (
        "_apogee_predictor_packet_queue",
        "_prediction_thread",
        "_processor_data_packet_queue",
    )

    def __init__(self) -> None:
        # Single input queue: main thread -> prediction thread
        self._processor_data_packet_queue: queue.SimpleQueue[
            ProcessorDataPacket | Literal["STOP"]
        ] = queue.SimpleQueue()

        self._apogee_predictor_packet_queue: queue.SimpleQueue[ApogeePredictorDataPacket] = (
            queue.SimpleQueue()
        )

        self._prediction_thread = threading.Thread(
            target=self._prediction_loop,
            name="Apogee Prediction Thread",
            daemon=True,
        )

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
        Gets the number of data packets in the FIRM data packet queue.

        :return: The number of FIRMDataPacket in the FIRM data packet
            queue.
        """
        return self._processor_data_packet_queue.qsize()

    def start(self) -> None:
        """
        Starts the prediction thread.

        This is called before the main loop starts.
        """
        if not self._prediction_thread.is_alive():
            self._prediction_thread.start()

    def stop(self) -> None:
        """Stops the prediction thread."""
        # Request the thread to stop:
        self._processor_data_packet_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        self._prediction_thread.join()

    def update(self, processor_data_packet: ProcessorDataPacket) -> None:
        """
        Updates the apogee predictor to include the most recent FIRM data
        packet.

        This method should only be called during the coast phase of the
        rocket's flight.

        :param processor_data_packet: The most recent FIRMDataPacket.
        """
        self._processor_data_packet_queue.put(processor_data_packet)

    def get_prediction_data_packet(self) -> ApogeePredictorDataPacket | None:
        """
        Gets the most recent apogee prediction data packet from the queue.

        This operation is non-blocking: it drains everything currently in the
        prediction queue and returns only the latest packet, or None if no
        prediction has been made yet.

        :return: The most recent ApogeePredictorDataPacket, or None.
        """
        apogee_predictor_packets = get_all_packets_from_queue(
            self._apogee_predictor_packet_queue, block=False
        )

        return apogee_predictor_packets[-1] if apogee_predictor_packets else None

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE THREAD -------------------------
    def _prediction_loop(self) -> None:
        """
        Responsible for fetching data packets, updating internal state, and
        finally predicting the apogee using the chosen method (e.g. HPRM).

        Runs in a separate thread.
        """
        rocket = Rocket(
            constants.ROCKET_DRY_MASS_KG,
            constants.ROCKET_CD,
            constants.ROCKET_CROSS_SECTIONAL_AREA_M2,
            constants.ROCKET_CROSS_SECTIONAL_AREA_M2,
            constants.ROCKET_MOMENT_OF_INERTIA_KG_M2,
            constants.ROCKET_STAB_MARGIN_DIMENSIONAL_M,
            constants.ROCKET_CL_A,
        )

        # Keep checking for new data packets until the stop signal is received:
        while True:
            processor_data_packets = get_all_packets_from_queue(
                self._processor_data_packet_queue, block=True
            )

            # If we got a stop signal in this batch, exit the loop
            if STOP_SIGNAL in processor_data_packets:
                break

            most_recent_packet = cast("ProcessorDataPacket", processor_data_packets[-1])

            # Compute apogee given the latest state and history

            initial_state = InitialState3DOF(
                x=0.0,
                y=most_recent_packet.current_altitude,
                angle=math.radians(most_recent_packet.tilt_angle_degrees),
                vx=most_recent_packet.horizontal_velocity_meters_per_s,
                vy=most_recent_packet.vertical_velocity_meters_per_s,
                angular_rate=most_recent_packet.angular_rate_deg_per_s,
                )

            apogee = rocket.predict_apogee_3dof(
                initial_state,
                integration_method=OdeMethod.RK45,
            )

            # Push a prediction packet back to the main thread.
            self._apogee_predictor_packet_queue.put(
                ApogeePredictorDataPacket(
                    apogee,
                    most_recent_packet.current_altitude,
                    most_recent_packet.vertical_velocity_meters_per_s,
                    most_recent_packet.horizontal_velocity_meters_per_s,
                    most_recent_packet.tilt_angle_degrees,
                    most_recent_packet.angular_rate_deg_per_s
                )
            )
