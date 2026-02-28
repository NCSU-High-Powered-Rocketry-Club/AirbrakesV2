"""Module for logging data to a CSV file in real time."""

import csv
import os
import queue
import threading
import typing
from collections import deque
from typing import Any, Literal

import msgspec

from airbrakes.constants import (
    IDLE_LOG_CAPACITY,
    LOG_BUFFER_SIZE,
    NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
    STOP_SIGNAL,
)
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.state import LandedState, StandbyState
from airbrakes.utils import get_all_packets_from_queue

if typing.TYPE_CHECKING:
    from pathlib import Path

    from firm_client import FIRMDataPacket

    from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
        ApogeePredictorDataPacket,
    )
    from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
    from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


DecodedLoggerDataPacket = list[int | float | str]
"""The type of LoggerDataPacket after an instance of it converted to primitive
type by msgspec.to_builtins."""


class Logger:
    """
    A class that logs data to a CSV file.

    The logging runs in a separate thread. This is because the logging
    thread is I/O-bound, meaning that it spends most of its time waiting
    for the file to be written to. By running it in a separate thread,
    we can continue to log data while the main loop is running. It uses
    Python's csv module to append the airbrakes' current state,
    extension, and FIRM data to our logs in real time.
    """

    __slots__ = (
        "_log_buffer",
        "_log_counter",
        "_log_queue",
        "_log_thread",
        "log_path",
    )

    def __init__(self, log_dir: Path) -> None:
        """
        Initializes the logger object.

        It creates a new log file in the specified directory. It creates
        a queue to store log messages, and starts a separate thread to
        handle the logging. We are logging a lot of data, and logging is
        I/O-bound, so running it in a separate thread allows the main
        loop to continue running without waiting for the log file to be
        written to.
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
        self._log_counter = 0
        self._log_buffer = deque(maxlen=LOG_BUFFER_SIZE)

        # Create a new log file with the next number in sequence
        self.log_path = log_dir / f"log_{max_suffix + 1}.csv"
        with self.log_path.open(mode="w", newline="") as file_writer:
            headers = list(LoggerDataPacket.__struct_fields__)
            writer = csv.writer(file_writer)
            writer.writerow(headers)

        self._log_queue: queue.SimpleQueue[LoggerDataPacket | Literal["STOP"]] = queue.SimpleQueue()

        # Start the logging thread
        self._log_thread = threading.Thread(
            target=self._logging_loop, name="Logger Thread", daemon=True
        )

    @property
    def is_running(self) -> bool:
        """Returns whether the logging thread is running."""
        return self._log_thread.is_alive()

    @property
    def is_log_buffer_full(self) -> bool:
        """Returns whether the log buffer is full."""
        return len(self._log_buffer) == LOG_BUFFER_SIZE

    @staticmethod
    def _convert_unknown_type_to_str(obj_type: Any) -> str:
        """
        Truncates the decimal place of the object to 8 decimal places.

        Used by msgspec to convert numpy float64 to a string.
        :param obj_type: The object to truncate.
        :return: The truncated object.
        """
        return f"{obj_type:.8f}"

    @staticmethod
    def _prepare_logger_packets(
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        firm_data_packets: list[FIRMDataPacket],
        apogee_predictor_data_packet: ApogeePredictorDataPacket | None,
    ) -> list[LoggerDataPacket]:
        """
        Creates a data packet representing a row of data to be logged.

        :param context_data_packet: The Context Data Packet to log.
        :param servo_data_packet: The Servo Data Packet to log.
        :param firm_data_packets: The FIRM data packets to log.
        :param apogee_predictor_data_packet: The most recent apogee
            predictor data packet to log.
        :return: A deque of LoggerDataPacket objects.
        """
        logger_data_packets: list[LoggerDataPacket] = []

        # zip the FIRM and Processor data packets together
        for firm_data_packet in firm_data_packets:
            # Apogee Predictor fields default to none if no packet is provided
            predicted_apogee = None
            height_used_for_prediction = None
            velocity_used_for_prediction = None

            if apogee_predictor_data_packet:
                predicted_apogee = apogee_predictor_data_packet.predicted_apogee
                height_used_for_prediction = apogee_predictor_data_packet.height_used_for_prediction
                velocity_used_for_prediction = (
                    apogee_predictor_data_packet.velocity_used_for_prediction
                )

            logger_packet = LoggerDataPacket(
                # Context and Servo Fields
                state_letter=context_data_packet.state.__name__[0],
                set_extension=str(servo_data_packet.set_extension.value),
                encoder_position=servo_data_packet.encoder_position,
                battery_voltage=servo_data_packet.battery_voltage,
                current_milliamps=servo_data_packet.current_milliamps,
                # FIRMDataPacket Fields
                timestamp_seconds=firm_data_packet.timestamp_seconds,
                temperature_celsius=firm_data_packet.temperature_celsius,
                pressure_pascals=firm_data_packet.pressure_pascals,
                raw_acceleration_x_gs=firm_data_packet.raw_acceleration_x_gs,
                raw_acceleration_y_gs=firm_data_packet.raw_acceleration_y_gs,
                raw_acceleration_z_gs=firm_data_packet.raw_acceleration_z_gs,
                raw_angular_rate_x_deg_per_s=firm_data_packet.raw_angular_rate_x_deg_per_s,
                raw_angular_rate_y_deg_per_s=firm_data_packet.raw_angular_rate_y_deg_per_s,
                raw_angular_rate_z_deg_per_s=firm_data_packet.raw_angular_rate_z_deg_per_s,
                magnetic_field_x_microteslas=firm_data_packet.magnetic_field_x_microteslas,
                magnetic_field_y_microteslas=firm_data_packet.magnetic_field_y_microteslas,
                magnetic_field_z_microteslas=firm_data_packet.magnetic_field_z_microteslas,
                est_position_x_meters=firm_data_packet.est_position_x_meters,
                est_position_y_meters=firm_data_packet.est_position_y_meters,
                est_position_z_meters=firm_data_packet.est_position_z_meters,
                est_velocity_x_meters_per_s=firm_data_packet.est_velocity_x_meters_per_s,
                est_velocity_y_meters_per_s=firm_data_packet.est_velocity_y_meters_per_s,
                est_velocity_z_meters_per_s=firm_data_packet.est_velocity_z_meters_per_s,
                est_acceleration_x_gs=firm_data_packet.est_acceleration_x_gs,
                est_acceleration_y_gs=firm_data_packet.est_acceleration_y_gs,
                est_acceleration_z_gs=firm_data_packet.est_acceleration_z_gs,
                est_angular_rate_x_rad_per_s=firm_data_packet.est_angular_rate_x_rad_per_s,
                est_angular_rate_y_rad_per_s=firm_data_packet.est_angular_rate_y_rad_per_s,
                est_angular_rate_z_rad_per_s=firm_data_packet.est_angular_rate_z_rad_per_s,
                est_quaternion_w=firm_data_packet.est_quaternion_w,
                est_quaternion_x=firm_data_packet.est_quaternion_x,
                est_quaternion_y=firm_data_packet.est_quaternion_y,
                est_quaternion_z=firm_data_packet.est_quaternion_z,
                # Apogee Predictor Data Packet Fields
                predicted_apogee=predicted_apogee,
                height_used_for_prediction=height_used_for_prediction,
                velocity_used_for_prediction=velocity_used_for_prediction,
                # Remaining Context Fields
                retrieved_firm_packets=context_data_packet.retrieved_firm_packets,
                apogee_predictor_queue_size=context_data_packet.apogee_predictor_queue_size,
                update_timestamp_ns=context_data_packet.update_timestamp_ns,
            )

            logger_data_packets.append(logger_packet)

        return logger_data_packets

    def start(self) -> None:
        """
        Starts the logging thread.

        This is called before the main while loop starts.
        """
        self._log_thread.start()

    def stop(self) -> None:
        """
        Stops the logging thread.

        It will finish logging the current message and then stop.
        """
        # Log the buffer before stopping the thread
        self._log_the_buffer()
        self._log_queue.put(STOP_SIGNAL)  # Put the stop signal in the queue
        # Waits for the thread to finish before stopping it
        self._log_thread.join()

    def log(
        self,
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        firm_data_packets: list[FIRMDataPacket],
        apogee_predictor_data_packet: ApogeePredictorDataPacket | None,
    ) -> None:
        """
        Logs the current state, extension, and FIRM data to the CSV file.

        :param context_data_packet: The Context Data Packet to log.
        :param servo_data_packet: The Servo Data Packet to log.
        :param firm_data_packets: The FIRM data packets to log.
        :param apogee_predictor_data_packet: The most recent apogee
            predictor data packet to log.
        """
        # We are populating a list with the fields of the logger data packet
        logger_data_packets: list[LoggerDataPacket] = Logger._prepare_logger_packets(
            context_data_packet,
            servo_data_packet,
            firm_data_packets,
            apogee_predictor_data_packet,
        )

        # If we are in Standby or Landed State, we need to buffer the data packets:
        if context_data_packet.state in (StandbyState, LandedState):
            # Determine how many packets to log and buffer
            log_capacity = max(0, IDLE_LOG_CAPACITY - self._log_counter)
            to_log = logger_data_packets[:log_capacity]
            to_buffer = logger_data_packets[log_capacity:]

            # Update counter and handle logging/buffering
            self._log_counter += len(to_log)
            if to_log:
                for packet in to_log:
                    self._log_queue.put(packet, block=False)
            if to_buffer:
                self._log_buffer.extend(to_buffer)
        else:
            # If we are not in Standby or Landed State, we should log the buffer if it's not empty:
            if self._log_buffer:
                self._log_the_buffer()

            # Reset the counter for other states
            self._log_counter = 0
            for packet in logger_data_packets:
                self._log_queue.put(packet, block=False)

    def _log_the_buffer(self):
        """
        Enqueues all the packets in the log buffer to the log queue, so they
        will be logged.
        """
        for packet in self._log_buffer:
            self._log_queue.put(packet, block=False)
        self._log_buffer.clear()

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE THREAD -------------------------
    @staticmethod
    def _truncate_floats(data: DecodedLoggerDataPacket) -> list[str | int]:
        """
        Truncates the decimal place of the floats in the list to 8 decimal
        places.

        :param data: The list of values whose floats we should truncate.
        :return: The truncated list.
        """
        return [f"{value:.8f}" if isinstance(value, float) else value for value in data]

    def _logging_loop(self) -> None:  # pragma: no cover
        """
        The loop that saves data to the logs.

        It runs in parallel with the main loop.
        """
        # Set up the csv logging in the new thread
        with self.log_path.open(mode="a", newline="") as file_writer:
            writer = csv.writer(file_writer)
            number_of_lines_logged = 0
            while True:
                # Get a message from the queue (this will block until a message is available)
                # Because there's no timeout, it will wait indefinitely until it gets a message.
                logger_packets: list[LoggerDataPacket | Literal["STOP"]] = (
                    get_all_packets_from_queue(self._log_queue, block=True)
                )
                packet_fields: list[DecodedLoggerDataPacket | Literal["STOP"]] = (
                    msgspec.to_builtins(
                        logger_packets, enc_hook=Logger._convert_unknown_type_to_str
                    )
                )
                # If the message is the stop signal, break out of the loop
                for message_field in packet_fields:
                    if message_field == STOP_SIGNAL:
                        return
                    writer.writerow(Logger._truncate_floats(message_field))
                    number_of_lines_logged += 1
                    # During our Pelicanator 1 flight, the rocket fell and had a very hard impact
                    # causing the pi to lose power. This caused us to lose a lot of lines of data
                    # that were not written to the log file. To prevent this from happening again,
                    # we flush the logger 1000 lines (equivalent to 1 second).
                    if number_of_lines_logged % NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING == 0:
                        # Tell Python to flush the data. This gives the data to the OS, and it is
                        # stored as a dirty page cache (in memory) until the OS decides to write it
                        # to disk. Technically python automatically flushes the data when the python
                        # buffer is full (8192 bytes, which would be about 25 lines of data).
                        file_writer.flush()
                        # Tell the OS to write the file to disk from the dirty page cache. This
                        # ensures that the data is written to disk and not just stored in memory.
                        # This operation is the one which is actually "blocking" when talking about
                        # file I/O.
                        os.fsync(file_writer.fileno())
