# cython: language_level=3
"""Module for logging data to a CSV file in real time."""

import csv
import multiprocessing
import signal
import sys
from collections import deque
from pathlib import Path
from typing import Any, Literal

from airbrakes.telemetry.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.telemetry.packets.servo_data_packet import ServoDataPacket
from airbrakes.utils import modify_multiprocessing_queue_windows

if sys.platform != "win32":
    from faster_fifo import Empty, Queue
else:
    from queue import Empty

import cython
import msgspec

from airbrakes.constants import (
    BUFFER_SIZE_IN_BYTES,
    IDLE_LOG_CAPACITY,
    LOG_BUFFER_SIZE,
    MAX_GET_TIMEOUT_SECONDS,
    STOP_SIGNAL,
)
from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket, IMUDataPacket
from airbrakes.telemetry.packets.logger_data_packet import LoggerDataPacket
from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket

DecodedLoggerDataPacket = list[int | float | str]
"""The type of LoggerDataPacket after an instance of it was decoded from the queue. It is
the same type as msgspec.to_builtins(LoggerDataPacket)."""


class Logger:
    """
    A class that logs data to a CSV file. Similar to the IMU class, it runs in a separate process.
    This is because the logging process is I/O-bound, meaning that it spends most of its time
    waiting for the file to be written to. By running it in a separate process, we can continue to
    log data while the main loop is running.

    It uses Python's csv module to append the airbrakes' current state, extension, and IMU data to
    our logs in real time.
    """

    __slots__ = (
        "_log_buffer",
        "_log_counter",
        "_log_process",
        "_log_queue",
        "log_path",
    )

    LOG_BUFFER_STATES = cython.declare(tuple[str, str], ("S", "L"))

    def __init__(self, log_dir: Path) -> None:
        """
        Initializes the logger object. It creates a new log file in the specified directory. Like
        the IMU class, it creates a queue to store log messages, and starts a separate process to
        handle the logging. We are logging a lot of data, and logging is I/O-bound, so running it
        in a separate process allows the main loop to continue running without waiting for the log
        file to be written to.
        :param log_dir: The directory where the log files will be.
        """
        # Create the log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Get all existing log files and find the highest suffix number
        existing_logs = list(log_dir.glob("log_*.csv"))
        max_suffix = (
            max(int(log.stem.split("_")[-1]) for log in existing_logs) if existing_logs else 0
        )

        # Buffer for StandbyState and LandedState
        self._log_counter: cython.uint = 0
        self._log_buffer = deque(maxlen=LOG_BUFFER_SIZE)

        # Create a new log file with the next number in sequence
        self.log_path = log_dir / f"log_{max_suffix + 1}.csv"
        with self.log_path.open(mode="w", newline="") as file_writer:
            headers = list(LoggerDataPacket.__struct_fields__)
            writer = csv.writer(file_writer)
            writer.writerow(headers)

        # Makes a queue to store log messages, basically it's a process-safe list that you add to
        # the back and pop from front, meaning that things will be logged in the order they were
        # added.
        # Signals (like stop) are sent as strings, but data is sent as dictionaries
        msgpack_encoder = msgspec.msgpack.Encoder(enc_hook=Logger._convert_unknown_type_to_str)
        # No need to specify the type to decode to, since we want to log it immediately, so a list
        # is wanted (and faster!):
        msgpack_decoder = msgspec.msgpack.Decoder()

        if sys.platform == "win32":
            # On Windows, we use a multiprocessing.Queue because the faster_fifo.Queue is not
            # available on Windows
            self._log_queue: multiprocessing.Queue[list[LoggerDataPacket] | Literal["STOP"]] = (
                multiprocessing.Queue()
            )
            modify_multiprocessing_queue_windows(self._log_queue)
        else:
            self._log_queue: Queue[list[LoggerDataPacket] | Literal["STOP"]] = Queue(
                max_size_bytes=BUFFER_SIZE_IN_BYTES,
                loads=msgpack_decoder.decode,
                dumps=msgpack_encoder.encode,
            )

        # Start the logging process
        self._log_process = multiprocessing.Process(
            target=self._logging_loop, name="Logger Process"
        )

    @property
    def is_running(self) -> bool:
        """
        Returns whether the logging process is running.
        """
        return self._log_process.is_alive()

    @property
    def is_log_buffer_full(self) -> bool:
        """
        Returns whether the log buffer is full.
        """
        return len(self._log_buffer) == LOG_BUFFER_SIZE

    @staticmethod
    def _convert_unknown_type_to_str(obj_type: Any) -> str:
        """
        Truncates the decimal place of the object to 8 decimal places. Used by msgspec to
        convert numpy float64 to a string.
        :param obj_type: The object to truncate.
        :return: The truncated object.
        """
        return f"{obj_type:.8f}"

    @staticmethod
    @cython.wraparound(False)  # Assume that the index is always positive (no negative indices)
    def _prepare_logger_packets(
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        imu_data_packets: list[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packets: list[ApogeePredictorDataPacket],
    ) -> list[LoggerDataPacket]:
        """
        Creates a data packet representing a row of data to be logged.
        :param context_data_packet: The context data packet to log.
        :param servo_data_packet: The servo data packet to log.
        :param imu_data_packets: The IMU data packets to log.
        :param processor_data_packets: The processor data packets to log. This is always the same
        length as the number of EstimatedDataPackets present in the `imu_data_packets`.
        :param apogee_predictor_data_packets: The apogee predictor data packets to log.
        :return: A deque of LoggerDataPacket objects.
        """
        logger_data_packets: list[LoggerDataPacket] = []

        est_packet_index: cython.Py_ssize_t = 0  # Index to loop over processor data packets:
        imu_data_packet_index: cython.Py_ssize_t  # Index to loop over IMU data packets
        data_packets_length: cython.Py_ssize_t = len(imu_data_packets)

        # Convert the imu data packets to a LoggerDataPacket:
        for imu_data_packet_index in range(data_packets_length):
            imu_data_packet = imu_data_packets[imu_data_packet_index]
            logger_packet = LoggerDataPacket(
                state_letter=context_data_packet.state_letter,
                set_extension=servo_data_packet.set_extension,
                encoder_position=servo_data_packet.encoder_position,
                timestamp=imu_data_packet.timestamp,
                invalid_fields=imu_data_packet.invalid_fields,
                fetched_packets_in_main=context_data_packet.fetched_packets_in_main,
                imu_queue_size=context_data_packet.imu_queue_size,
                apogee_predictor_queue_size=context_data_packet.apogee_predictor_queue_size,
                fetched_imu_packets=context_data_packet.fetched_imu_packets,
                update_timestamp_ns=context_data_packet.update_timestamp_ns,
            )

            # Get the IMU data packet fields:
            # Performance comparison (python 3.13.1 on x86_64 linux):
            # - isinstance is 45.2% faster than match statement
            # - hasattr is 20.57% faster than isinstance
            # - type() is 34.85% faster than hasattr
            if type(imu_data_packet) is EstimatedDataPacket:
                # Extract all the fields from the EstimatedDataPacket
                logger_packet.estOrientQuaternionW = imu_data_packet.estOrientQuaternionW
                logger_packet.estOrientQuaternionX = imu_data_packet.estOrientQuaternionX
                logger_packet.estOrientQuaternionY = imu_data_packet.estOrientQuaternionY
                logger_packet.estOrientQuaternionZ = imu_data_packet.estOrientQuaternionZ
                logger_packet.estPressureAlt = imu_data_packet.estPressureAlt
                logger_packet.estAttitudeUncertQuaternionW = (
                    imu_data_packet.estAttitudeUncertQuaternionW
                )
                logger_packet.estAttitudeUncertQuaternionX = (
                    imu_data_packet.estAttitudeUncertQuaternionX
                )
                logger_packet.estAttitudeUncertQuaternionY = (
                    imu_data_packet.estAttitudeUncertQuaternionY
                )
                logger_packet.estAttitudeUncertQuaternionZ = (
                    imu_data_packet.estAttitudeUncertQuaternionZ
                )
                logger_packet.estAngularRateX = imu_data_packet.estAngularRateX
                logger_packet.estAngularRateY = imu_data_packet.estAngularRateY
                logger_packet.estAngularRateZ = imu_data_packet.estAngularRateZ
                logger_packet.estCompensatedAccelX = imu_data_packet.estCompensatedAccelX
                logger_packet.estCompensatedAccelY = imu_data_packet.estCompensatedAccelY
                logger_packet.estCompensatedAccelZ = imu_data_packet.estCompensatedAccelZ
                logger_packet.estLinearAccelX = imu_data_packet.estLinearAccelX
                logger_packet.estLinearAccelY = imu_data_packet.estLinearAccelY
                logger_packet.estLinearAccelZ = imu_data_packet.estLinearAccelZ
                logger_packet.estGravityVectorX = imu_data_packet.estGravityVectorX
                logger_packet.estGravityVectorY = imu_data_packet.estGravityVectorY
                logger_packet.estGravityVectorZ = imu_data_packet.estGravityVectorZ

                # Now also extract the fields from the ProcessorDataPacket
                logger_packet.current_altitude = processor_data_packets[
                    est_packet_index
                ].current_altitude
                logger_packet.vertical_velocity = processor_data_packets[
                    est_packet_index
                ].vertical_velocity
                logger_packet.vertical_acceleration = processor_data_packets[
                    est_packet_index
                ].vertical_acceleration

                # Add index:
                est_packet_index += 1
            else:  # It is a raw packet:
                # Extract all the fields from the RawDataPacket
                logger_packet.scaledAccelX = imu_data_packet.scaledAccelX
                logger_packet.scaledAccelY = imu_data_packet.scaledAccelY
                logger_packet.scaledAccelZ = imu_data_packet.scaledAccelZ
                logger_packet.scaledGyroX = imu_data_packet.scaledGyroX
                logger_packet.scaledGyroY = imu_data_packet.scaledGyroY
                logger_packet.scaledGyroZ = imu_data_packet.scaledGyroZ
                logger_packet.deltaVelX = imu_data_packet.deltaVelX
                logger_packet.deltaVelY = imu_data_packet.deltaVelY
                logger_packet.deltaVelZ = imu_data_packet.deltaVelZ
                logger_packet.deltaThetaX = imu_data_packet.deltaThetaX
                logger_packet.deltaThetaY = imu_data_packet.deltaThetaY
                logger_packet.deltaThetaZ = imu_data_packet.deltaThetaZ
                logger_packet.scaledAmbientPressure = imu_data_packet.scaledAmbientPressure

            # Apogee Prediction happens asynchronously, so we need to check if we have a packet:

            # There is a small possibility that we won't log all the apogee predictor data packets
            # if the length of the IMU data packets is less than the length of the apogee predictor
            # data packets. However, this is unlikely to happen in practice. This particular case
            # is NOT covered by tests.
            if apogee_predictor_data_packets:
                apogee_packet = apogee_predictor_data_packets.pop(0)
                logger_packet.predicted_apogee = apogee_packet.predicted_apogee
                logger_packet.a_coefficient = apogee_packet.a_coefficient
                logger_packet.b_coefficient = apogee_packet.b_coefficient
                logger_packet.uncertainty_threshold_1 = apogee_packet.uncertainty_threshold_1
                logger_packet.uncertainty_threshold_2 = apogee_packet.uncertainty_threshold_2

            logger_data_packets.append(logger_packet)

        return logger_data_packets

    def start(self) -> None:
        """
        Starts the logging process. This is called before the main while loop starts.
        """
        self._log_process.start()

    def stop(self) -> None:
        """
        Stops the logging process. It will finish logging the current message and then stop.
        """
        # Log the buffer before stopping the process
        self._log_the_buffer()
        self._log_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        # Waits for the process to finish before stopping it
        self._log_process.join()

    def log(
        self,
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        imu_data_packets: list[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packets: list[ApogeePredictorDataPacket],
    ) -> None:
        """
        Logs the current state, extension, and IMU data to the CSV file.
        :param context_data_packet: The context data packet to log.
        :param servo_data_packet: The servo data packet to log.
        :param imu_data_packets: The IMU data packets to log.
        :param processor_data_packets: The processor data packets to log.
        :param apogee_predictor_data_packets: The apogee predictor data packets to log.
        """
        # We are populating a list with the fields of the logger data packet
        logger_data_packets: list[LoggerDataPacket] = Logger._prepare_logger_packets(
            context_data_packet,
            servo_data_packet,
            imu_data_packets,
            processor_data_packets,
            apogee_predictor_data_packets,
        )

        # If we are in Standby or Landed State, we need to buffer the data packets:
        if context_data_packet.state_letter in self.LOG_BUFFER_STATES:
            # Determine how many packets to log and buffer
            log_capacity = max(0, IDLE_LOG_CAPACITY - self._log_counter)
            to_log = logger_data_packets[:log_capacity]
            to_buffer = logger_data_packets[log_capacity:]

            # Update counter and handle logging/buffering
            self._log_counter += len(to_log)
            if to_log:
                self._log_queue.put_many(to_log)
            if to_buffer:
                self._log_buffer.extend(to_buffer)
        else:
            # If we are not in Standby or Landed State, we should log the buffer if it's not empty:
            if self._log_buffer:
                self._log_the_buffer()

            # Reset the counter for other states
            self._log_counter = 0
            self._log_queue.put_many(logger_data_packets)

    def _log_the_buffer(self):
        """
        Adds the log buffer to the queue, so it can be logger to file.
        """
        self._log_queue.put_many(list(self._log_buffer))
        self._log_buffer.clear()

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE PROCESS -------------------------
    @staticmethod
    def _truncate_floats(data: DecodedLoggerDataPacket) -> list[str | int]:
        """
        Truncates the decimal place of the floats in the list to 8 decimal places.
        :param data: The list of values whose floats we should truncate.
        :return: The truncated list.
        """
        return [f"{value:.8f}" if isinstance(value, float) else value for value in data]

    def _logging_loop(self) -> None:  # pragma: no cover
        """
        The loop that saves data to the logs. It runs in parallel with the main loop.
        """
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal

        # Unfortunately, we need to modify the queue here again because the modifications made in
        # the __init__ are not copied to the new process.
        modify_multiprocessing_queue_windows(self._log_queue)

        # Set up the csv logging in the new process
        with self.log_path.open(mode="a", newline="") as file_writer:
            writer = csv.writer(file_writer)
            while True:
                # Get a message from the queue (this will block until a message is available)
                # Because there's no timeout, it will wait indefinitely until it gets a message.
                try:
                    message_fields: list[DecodedLoggerDataPacket | Literal["STOP"]] = (
                        self._log_queue.get_many(timeout=MAX_GET_TIMEOUT_SECONDS)
                    )
                except Empty:
                    continue
                # If the message is the stop signal, break out of the loop
                for message_field in message_fields:
                    if message_field == STOP_SIGNAL:
                        return
                    writer.writerow(Logger._truncate_floats(message_field))
