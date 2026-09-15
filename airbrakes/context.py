"""High-level interface coordinating the airbrakes flight system."""

import time
from typing import TYPE_CHECKING

from airbrakes.constants import (
    BUSY_WAIT_SECONDS,
    SERVO_EXTENSION_TOLERANCE,
    SERVO_MIN_EXTENSION,
)
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket
from airbrakes.state import StandbyState

if TYPE_CHECKING:
    from airbrakes.base_classes.base_imu import BaseIMU
    from airbrakes.base_classes.base_servo import BaseServo
    from airbrakes.data_handling.apogee_predictor import ApogeePredictor
    from airbrakes.data_handling.data_processor import DataProcessor
    from airbrakes.data_handling.logger import Logger
    from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
        ApogeePredictorDataPacket,
    )
    from airbrakes.data_handling.packets.imu_data_packet import IMUDataPacket
    from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
    from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket
    from airbrakes.state import State


class Context:
    """Connect hardware, processing, logging, prediction, and the flight state machine."""

    __slots__ = (
        "apogee_predictor",
        "context_data_packet",
        "data_processor",
        "est_data_packets",
        "imu",
        "imu_data_packets",
        "launch_time_seconds",
        "logger",
        "most_recent_apogee_predictor_data_packet",
        "processor_data_packets",
        "servo",
        "servo_data_packet",
        "shutdown_requested",
        "state",
    )

    def __init__(
        self,
        servo: BaseServo,
        imu: BaseIMU,
        logger: Logger,
        data_processor: DataProcessor,
        apogee_predictor: ApogeePredictor,
    ) -> None:
        self.servo = servo
        self.imu = imu
        self.logger = logger
        self.data_processor = data_processor
        self.apogee_predictor = apogee_predictor
        self.state: State = StandbyState(self)

        self.shutdown_requested = False
        self.imu_data_packets: list[IMUDataPacket] = []
        self.est_data_packets: list[EstimatedDataPacket] = []
        self.processor_data_packets: list[ProcessorDataPacket] = []
        self.most_recent_apogee_predictor_data_packet: ApogeePredictorDataPacket | None = None
        self.context_data_packet: ContextDataPacket | None = None
        self.servo_data_packet: ServoDataPacket | None = None
        self.launch_time_seconds = 0.0

    def start(self, wait_for_start: bool = False) -> None:
        """Start all components required for a flight."""
        self.imu.start()
        self.logger.start()
        self.apogee_predictor.start()
        self.servo.start()
        self.servo.retract_airbrakes()

        if wait_for_start:
            while not self.imu.is_running:
                time.sleep(BUSY_WAIT_SECONDS)

    def stop(self) -> None:
        """Retract airbrakes and stop every running flight component."""
        if self.shutdown_requested:
            return
        self.shutdown_requested = True
        self.retract_airbrakes()
        self.imu.stop()
        self.logger.stop()
        self.apogee_predictor.stop()
        self.servo.stop()

    def update(self) -> None:
        """Consume a batch of IMU data, process it, advance state, and log it."""
        # TODO: add all comments back
        self.imu_data_packets = self.imu.get_imu_data_packets()
        if not self.imu_data_packets:
            return

        self.est_data_packets = [
            packet for packet in self.imu_data_packets if isinstance(packet, EstimatedDataPacket)
        ]

        # TODO: figure out what to do for the zeroing altitude
        # if self.est_data_packets:
        #     self.data_processor.update(self.est_data_packets)
        #     if isinstance(self.state, StandbyState):
        #         self.data_processor.zero_out_altitude()
        #     self.processor_data_packets = self.data_processor.get_processor_data_packets()

        # Update the data processor with the new data packets.
        self.data_processor.update(self.est_data_packets)

        # Get the Processor Data Packets from the data processor, this will have the same length
        # as the number of EstimatedDataPackets in data_packets because a processor data packet is
        # created for each estimated data packet.
        # TODO: figure out of this is a good idea or not, it's nice because we don't want to do
        # prediction if we don't have any estimated data packets/new processor data packets
        # self.processor_data_packets = []
        if self.est_data_packets:
            self.processor_data_packets = self.data_processor.get_processor_data_packets()

        apogee_prediction_packet = self.apogee_predictor.get_prediction_data_packet()
        if apogee_prediction_packet:
            self.most_recent_apogee_predictor_data_packet = apogee_prediction_packet

        self.state.update()
        self.generate_data_packets()

        if self.context_data_packet is not None and self.servo_data_packet is not None:
            self.logger.log(
                self.context_data_packet,
                self.servo_data_packet,
                self.imu_data_packets,
                self.processor_data_packets,
                self.most_recent_apogee_predictor_data_packet,
            )

    def extend_airbrakes(self, velocity: float) -> None:
        """Extend airbrakes using the current vertical velocity."""
        self.data_processor.prepare_for_extending_airbrakes()
        self.servo.extend_airbrakes(velocity)

    def retract_airbrakes(self) -> None:
        """Retract airbrakes if they are not already at the minimum extension."""
        if abs(self.servo.servo_extension - SERVO_MIN_EXTENSION) > SERVO_EXTENSION_TOLERANCE:
            self.data_processor.prepare_for_retracting_airbrakes()
            self.servo.retract_airbrakes()

    def predict_apogee(self) -> None:
        """Queue the latest processed IMU value for HPRM apogee prediction."""
        # TODO: see if we should change this to processed_data_packets
        if self.est_data_packets:
            self.apogee_predictor.update(self.processor_data_packets[-1])

    def generate_data_packets(self) -> None:
        """Create context and servo packets for the current update."""
        self.context_data_packet = ContextDataPacket(
            state=type(self.state),
            retrieved_imu_packets=len(self.imu_data_packets),
            queued_imu_packets=self.imu.queued_imu_packets,
            imu_packets_per_cycle=self.imu.imu_packets_per_cycle,
            apogee_predictor_queue_size=self.apogee_predictor.processor_data_packet_queue_size,
            update_timestamp_ns=time.time_ns(),
        )
        self.servo_data_packet = self.servo.get_servo_data_packet()
