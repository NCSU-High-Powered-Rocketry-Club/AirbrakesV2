"""Real-time CSV logging for IMU and airbrakes data."""

import csv
import os
import queue
import threading
from collections import deque
from typing import TYPE_CHECKING, Any, Literal

import msgspec
from msgspec.structs import asdict

from airbrakes.constants import (
    IDLE_LOG_CAPACITY,
    LOG_BUFFER_SIZE,
    NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING,
    STOP_SIGNAL,
)
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket
from airbrakes.state import LandedState, StandbyState
from airbrakes.utils import get_all_packets_from_queue

if TYPE_CHECKING:
    from pathlib import Path

    from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
        ApogeePredictorDataPacket,
    )
    from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
    from airbrakes.data_handling.packets.imu_data_packet import IMUDataPacket
    from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
    from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket

DecodedLoggerDataPacket = list[int | float | str]


class Logger:
    """Log IMU packets and airbrakes state to a CSV file from a dedicated thread."""

    __slots__ = ("_log_buffer", "_log_counter", "_log_queue", "_log_thread", "log_path")

    def __init__(self, log_dir: Path) -> None:
        log_dir.mkdir(parents=True, exist_ok=True)
        existing_logs = list(log_dir.glob("log_*.csv"))
        max_suffix = (
            max(int(log.stem.split("_")[-1]) for log in existing_logs) if existing_logs else 0
        )
        self._log_counter = 0
        self._log_buffer: deque[LoggerDataPacket] = deque(maxlen=LOG_BUFFER_SIZE)
        self.log_path = log_dir / f"log_{max_suffix + 1}.csv"
        with self.log_path.open(mode="w", newline="") as file_writer:
            csv.writer(file_writer).writerow(LoggerDataPacket.__struct_fields__)

        self._log_queue: queue.SimpleQueue[LoggerDataPacket | Literal["STOP"]] = queue.SimpleQueue()
        self._log_thread = threading.Thread(
            target=self._logging_loop, name="Logger Thread", daemon=True
        )

    @property
    def is_running(self) -> bool:
        """Return whether the logging thread is running."""
        return self._log_thread.is_alive()

    @property
    def is_log_buffer_full(self) -> bool:
        """Return whether the idle-state log buffer has reached capacity."""
        return len(self._log_buffer) == LOG_BUFFER_SIZE

    @staticmethod
    def _convert_unknown_type_to_str(obj_type: Any) -> str:
        return f"{obj_type:.8f}"

    @staticmethod
    def _prepare_logger_packets(
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        imu_data_packets: list[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packet: ApogeePredictorDataPacket | None,
    ) -> list[LoggerDataPacket]:
        """Create one log row for each raw or estimated IMU packet."""
        estimated_packet_count = sum(
            isinstance(packet, EstimatedDataPacket) for packet in imu_data_packets
        )
        if len(processor_data_packets) != estimated_packet_count:
            raise ValueError("Processor data packets must align with estimated IMU data packets.")

        context_values = asdict(context_data_packet)
        state = context_values.pop("state")
        servo_values = asdict(servo_data_packet)
        prediction_values = (
            asdict(apogee_predictor_data_packet) if apogee_predictor_data_packet is not None else {}
        )
        processed_packets = iter(processor_data_packets)
        logger_packets: list[LoggerDataPacket] = []

        for imu_data_packet in imu_data_packets:
            processor_values = (
                asdict(next(processed_packets))
                if isinstance(imu_data_packet, EstimatedDataPacket)
                else {}
            )
            logger_packets.append(
                LoggerDataPacket(
                    state_letter=state.__name__[0],
                    **servo_values,
                    **asdict(imu_data_packet),
                    **processor_values,
                    **prediction_values,
                    **context_values,
                )
            )
        return logger_packets

    def start(self) -> None:
        """Start the logging thread."""
        self._log_thread.start()

    def stop(self) -> None:
        """Flush buffered rows and stop the logging thread."""
        self._log_the_buffer()
        self._log_queue.put(STOP_SIGNAL)
        self._log_thread.join()

    def log(
        self,
        context_data_packet: ContextDataPacket,
        servo_data_packet: ServoDataPacket,
        imu_data_packets: list[IMUDataPacket],
        processor_data_packets: list[ProcessorDataPacket],
        apogee_predictor_data_packet: ApogeePredictorDataPacket | None,
    ) -> None:
        """Queue log rows, buffering limited standby and landed data."""
        logger_packets = self._prepare_logger_packets(
            context_data_packet,
            servo_data_packet,
            imu_data_packets,
            processor_data_packets,
            apogee_predictor_data_packet,
        )
        if context_data_packet.state in (StandbyState, LandedState):
            log_capacity = max(0, IDLE_LOG_CAPACITY - self._log_counter)
            to_log = logger_packets[:log_capacity]
            self._log_counter += len(to_log)
            for packet in to_log:
                self._log_queue.put(packet)
            self._log_buffer.extend(logger_packets[log_capacity:])
            return

        if self._log_buffer:
            self._log_the_buffer()
        self._log_counter = 0
        for packet in logger_packets:
            self._log_queue.put(packet)

    def _log_the_buffer(self) -> None:
        for packet in self._log_buffer:
            self._log_queue.put(packet)
        self._log_buffer.clear()

    @staticmethod
    def _truncate_floats(data: DecodedLoggerDataPacket) -> list[str | int]:
        return [f"{value:.8f}" if isinstance(value, float) else value for value in data]

    def _logging_loop(self) -> None:  # pragma: no cover
        with self.log_path.open(mode="a", newline="") as file_writer:
            writer = csv.writer(file_writer)
            number_of_lines_logged = 0
            while True:
                logger_packets = get_all_packets_from_queue(self._log_queue, block=True)
                packet_fields = msgspec.to_builtins(
                    logger_packets, enc_hook=Logger._convert_unknown_type_to_str
                )
                for message_field in packet_fields:
                    if message_field == STOP_SIGNAL:
                        return
                    writer.writerow(self._truncate_floats(message_field))
                    number_of_lines_logged += 1
                    if number_of_lines_logged % NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING == 0:
                        file_writer.flush()
                        os.fsync(file_writer.fileno())
