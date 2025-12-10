"""
Module for predicting apogee.
"""

import queue
import threading
from typing import TYPE_CHECKING, Literal, cast

from hprm import AdaptiveTimeStep, ModelType, OdeMethod, Rocket

from airbrakes.constants import ROCKET_CROSS_SECTIONAL_AREA_M2, ROCKET_MASS_KG, STOP_SIGNAL
from airbrakes.telemetry.packets.apogee_predictor_data_packet import (
    ApogeePredictorDataPacket,
)

if TYPE_CHECKING:
    from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket


class ApogeePredictor:
    """
    Class that performs the calculations to predict the apogee of the rocket during flight.
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
        Gets the number of data packets in the processor data packet queue.

        :return: The number of ProcessorDataPacket in the processor data packet queue.
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
        """
        Stops the prediction thread.
        """
        # Request the thread to stop:
        self._processor_data_packet_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        self._prediction_thread.join()

    def update(self, processor_data_packet: ProcessorDataPacket) -> None:
        """
        Updates the apogee predictor to include the most recent processor data packet.

        This method should only be called during the coast phase of the rocket's flight.

        :param processor_data_packet: The most recent ProcessorDataPacket.
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
        last_packet: ApogeePredictorDataPacket | None = None

        while True:
            try:
                packet = self._apogee_predictor_packet_queue.get_nowait()
            except queue.Empty:
                break
            else:
                last_packet = packet

        return last_packet

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE THREAD -------------------------
    def _prediction_loop(self) -> None:
        """
        Responsible for fetching data packets, updating internal state, and finally predicting
        the apogee using the chosen method (e.g. HPRM).

        Runs in a separate thread.
        """
        rocket = Rocket(
            ROCKET_MASS_KG,
            ROCKET_MASS_KG,
            ROCKET_CROSS_SECTIONAL_AREA_M2,
            # Rest of these are unused for 1D modeling
            0.0,
            0.0,
            0.0,
            0.0,
        )

        # Keep checking for new data packets until the stop signal is received:
        while True:
            # Block until at least one item (data packet or STOP_SIGNAL) is available
            first_item = self._processor_data_packet_queue.get()

            processor_data_packets: list[ProcessorDataPacket | Literal["STOP"]] = [first_item]

            # Drain any other items that have accumulated so we process a batch at once
            while True:
                try:
                    processor_data_packets.append(self._processor_data_packet_queue.get_nowait())
                except queue.Empty:
                    break

            # If we got a stop signal in this batch, exit the loop
            if STOP_SIGNAL in processor_data_packets:
                break

            most_recent_packet = cast("ProcessorDataPacket", processor_data_packets[-1])

            # Compute apogee given the latest state and history
            apogee = rocket.predict_apogee(
                most_recent_packet.current_altitude,
                most_recent_packet.velocity_magnitude,
                ModelType.OneDOF,
                OdeMethod.RK45,
                AdaptiveTimeStep(),
            )

            # Push a prediction packet back to the main thread.
            # TODO: add more stuff to the packet
            self._apogee_predictor_packet_queue.put(
                ApogeePredictorDataPacket(
                    apogee,
                    most_recent_packet.current_altitude,
                    most_recent_packet.velocity_magnitude,
                )
            )
