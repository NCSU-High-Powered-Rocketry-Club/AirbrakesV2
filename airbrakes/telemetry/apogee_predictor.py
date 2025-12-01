"""
Module for predicting apogee.
"""

import multiprocessing
import signal
from collections import deque
from typing import Literal

import msgspec
import msgspec.msgpack
import numpy as np
import numpy.typing as npt
from faster_fifo import (  # ty: ignore[unresolved-import]  no type hints for this library
    Empty,
    Queue,
)

from airbrakes.constants import (
    BUFFER_SIZE_IN_BYTES,
    MAX_GET_TIMEOUT_SECONDS,
    STOP_SIGNAL,
)
from airbrakes.telemetry.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.utils import convert_unknown_type_to_float


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
        "_prediction_process",
        "_processor_data_packet_queue",
        "_time_differences",
        "lookup_table",
    )

    def __init__(self):
        # ------ Variables which can referenced in the main process ------
        self._processor_data_packet_queue: Queue[ProcessorDataPacket | Literal["STOP"]] = Queue(
            max_size_bytes=BUFFER_SIZE_IN_BYTES,
        )
        self._apogee_predictor_packet_queue: Queue[ApogeePredictorDataPacket] = Queue(
            max_size_bytes=BUFFER_SIZE_IN_BYTES,
        )

        self._prediction_process = multiprocessing.Process(
            target=self._prediction_loop, name="Apogee Prediction Process"
        )

        # ------ Variables which can only be referenced in the prediction process ------
        self._cumulative_time_differences: npt.NDArray[np.float64] = np.array([])
        # list of all the accelerations since motor burn out:
        self._accelerations: deque[np.float64] = deque()
        # list of all the dt's since motor burn out
        self._time_differences: deque[np.float64] = deque()
        self._current_altitude: np.float64 = np.float64(0.0)
        self._current_velocity: np.float64 = np.float64(0.0)  # Velocity in the upwards axis
        self._has_apogee_converged: bool = False
        self._initial_velocity = None
        # ------------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        """
        Returns whether the prediction process is running.

        :return: True if the process is running, False otherwise.
        """
        return self._prediction_process.is_alive()

    @property
    def processor_data_packet_queue_size(self) -> int:
        """
        Gets the number of data packets in the processor data packet queue :return: The number of
        ProcessorDataPacket in the processor data packet queue.
        """
        return self._processor_data_packet_queue.qsize()

    def start(self) -> None:
        """
        Starts the prediction process.

        This is called before the main loop starts.
        """
        self._prediction_process.start()
        self._setup_queue_serialization_method()

    def stop(self) -> None:
        """
        Stops the prediction process.
        """
        # Waits for the process to finish before stopping it
        self._processor_data_packet_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        self._prediction_process.join()

    def update(self, processor_data_packet: ProcessorDataPacket) -> None:
        """
        Updates the apogee predictor to include the most recent processor data packet.

        This method should only be called during the coast phase of the rocket's flight.
        :param processor_data_packet: The most recent processor data packet.
        """
        self._processor_data_packet_queue.put(processor_data_packet)

    def get_prediction_data_packet(self) -> ApogeePredictorDataPacket:
        """
        Gets *all* of the apogee prediction data packets from the queue.

        This operation is non-blocking.
        :return: A list of the most recent apogee prediction data packets.
        """
        total_packets = []
        # get_many doesn't actually get all of the packets, so we need to keep checking until
        # there are no more packets left
        while self._apogee_predictor_packet_queue.qsize() > 0:
            new_packets = self._apogee_predictor_packet_queue.get_many(block=False)
            total_packets.extend(new_packets)
        return total_packets[-1]  # Return only the most recent packet
        # TODO: qsize isn't necessarily reliable, so we may need to implement a different method:
        # total_packets: list[ApogeePredictorDataPacket] = []
        #     while True:
        #         try:
        #             new_packets = self._apogee_predictor_packet_queue.get_many(block=False)
        #         except Empty:
        #             break
        #         if not new_packets:
        #             break
        #         total_packets.extend(new_packets)
        #     return total_packets

    def _setup_queue_serialization_method(self) -> None:
        """
        Sets up the serialization methods for the queued packets for faster-fifo.

        This is not done in the __init__ because "spawn" or "forkserver" will attempt to pickle the
        msgpack encoder and decoder, which will fail. Thus, we do it for the main and child process
        after the child has been born.
        """
        msgpack_encoder = msgspec.msgpack.Encoder(enc_hook=convert_unknown_type_to_float)
        msgpack_apg_data_packet_decoder = msgspec.msgpack.Decoder(type=ApogeePredictorDataPacket)
        msgpack_processor_data_packet_decoder = msgspec.msgpack.Decoder(
            type=ProcessorDataPacket | str
        )

        self._processor_data_packet_queue.dumps = msgpack_encoder.encode
        self._processor_data_packet_queue.loads = msgpack_processor_data_packet_decoder.decode

        self._apogee_predictor_packet_queue.dumps = msgpack_encoder.encode
        self._apogee_predictor_packet_queue.loads = msgpack_apg_data_packet_decoder.decode

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE PROCESS -------------------------
    def _prediction_loop(self) -> None:
        """
        Responsible for fetching data packets, curve fitting, updating our lookup table, and finally
        predicting the apogee.

        Runs in a separate process.
        """
        self._setup_queue_serialization_method()

        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal

        # Makes placeholder values for TODO
        apogee = 0.0

        # Keep checking for new data packets until the stop signal is received:
        while True:
            # Rather than having the queue store all the data packets, it is only used to
            # communicate between the main process and the prediction process. The main process
            # will add the data packets to the queue, and the prediction process will get the data
            # packets from the queue and add them to its own arrays.
            try:
                data_packets: list[ProcessorDataPacket | Literal["STOP"]] = (
                    self._processor_data_packet_queue.get_many(timeout=MAX_GET_TIMEOUT_SECONDS)
                )
            except Empty:
                continue

            if STOP_SIGNAL in data_packets:
                break

            apogee = self._predict_apogee(data_packets[-1])

            # Get the most recent packet, predict apogee, and send it to the apogee predictor queue
            # TODO: this is a placeholder until the apogee prediction is implemented
            # self._apogee_predictor_packet_queue.put(
            #     ApogeePredictorDataPacket(
            #         predicted_apogee=apogee,
            #         a_coefficient=curve_coefficients.A,
            #         b_coefficient=curve_coefficients.B,
            #         uncertainty_threshold_1=curve_coefficients.uncertainties[0],
            #         uncertainty_threshold_2=curve_coefficients.uncertainties[1],
            #     )
            # )

    def _predict_apogee(self, most_recent_processor_data_packet: ProcessorDataPacket) -> np.float64:
        """
        TODO.
        """
        # Use hprm
