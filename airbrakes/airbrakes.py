"""Module which provides a high level interface to the air brakes system on the rocket."""

import time
from typing import TYPE_CHECKING

from airbrakes.hardware.base_imu import BaseIMU
from airbrakes.hardware.camera import Camera
from airbrakes.hardware.servo import Servo
from airbrakes.state import StandbyState, State
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import IMUDataProcessor
from airbrakes.telemetry.logger import Logger
from airbrakes.telemetry.packets.apogee_predictor_data_packet import (
    ApogeePredictorDataPacket,
)
from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket
from airbrakes.telemetry.packets.servo_data_packet import ServoDataPacket
from airbrakes.utils import set_process_priority

if TYPE_CHECKING:
    from airbrakes.hardware.imu import IMUDataPacket
    from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket


class AirbrakesContext:
    """
    Manages the state machine for the rocket's airbrakes system, keeping track of the current state
    and communicating with hardware like the servo and IMU. This class is what connects the state
    machine to the hardware.

    Read more about the state machine pattern here:
    https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

    __slots__ = (
        "apogee_predictor",
        "apogee_predictor_data_packets",
        "camera",
        "context_data_packet",
        "data_processor",
        "est_data_packets",
        "imu",
        "imu_data_packets",
        "last_apogee_predictor_packet",
        "logger",
        "processor_data_packets",
        "servo",
        "servo_data_packet",
        "shutdown_requested",
        "state",
    )

    def __init__(
        self,
        servo: Servo,
        imu: BaseIMU,
        camera: Camera,
        logger: Logger,
        data_processor: IMUDataProcessor,
        apogee_predictor: ApogeePredictor,
    ) -> None:
        """
        Initializes the airbrakes context with the specified hardware objects, logger, and data
        processor. The state machine starts in the StandbyState, which is the initial state of the
        airbrakes system.
        :param servo: The servo object that controls the extension of the airbrakes. This can be a
        real servo or a mocked servo.
        :param imu: The IMU object that reads data from the rocket's IMU. This can be a real IMU or
        a mock IMU.
        :param camera: The camera object that records video from the rocket.
        :param logger: The logger object that logs data to a CSV file.
        :param data_processor: The data processor object that processes IMU data on a higher level.
        :param apogee_predictor: The apogee predictor object that predicts the apogee of the rocket.
        """
        self.servo: Servo = servo
        self.imu: BaseIMU = imu
        self.camera: Camera = camera
        self.logger: Logger = logger
        self.data_processor: IMUDataProcessor = data_processor
        self.apogee_predictor: ApogeePredictor = apogee_predictor
        # The rocket starts in the StandbyState
        self.state: State = StandbyState(self)

        self.shutdown_requested = False
        self.imu_data_packets: list[IMUDataPacket] = []
        self.processor_data_packets: list[ProcessorDataPacket] = []
        self.apogee_predictor_data_packets: list[ApogeePredictorDataPacket] = []
        self.est_data_packets: list[EstimatedDataPacket] = []
        self.context_data_packet: ContextDataPacket | None = None
        self.servo_data_packet: ServoDataPacket | None = None
        self.last_apogee_predictor_packet = ApogeePredictorDataPacket(0, 0, 0, 0, 0)

    def start(self) -> None:
        """
        Starts the IMU and logger processes. This is called before the main while loop starts.
        """
        set_process_priority(-5)  # Higher than normal priority
        self.imu.start()
        self.logger.start()
        self.apogee_predictor.start()
        self.camera.start()

    def stop(self) -> None:
        """
        Handles shutting down the airbrakes. This will cause the main loop to break. It retracts
        the airbrakes, stops the IMU, and stops the logger.
        """
        if self.shutdown_requested:
            return
        self.retract_airbrakes()
        self.imu.stop()
        self.logger.stop()
        self.apogee_predictor.stop()
        self.camera.stop()
        self.shutdown_requested = True

    def update(self) -> None:
        """
        Called every loop iteration from the main process. Depending on the current state, it will
        do different things. It is what controls the airbrakes and chooses when to move to the next
        state.
        """
        # get_imu_data_packets() gets from the "first" item in the queue, i.e, the set of data
        # *may* not be the most recent data. But we want continuous data for state, apogee,
        # and logging purposes, so we don't need to worry about that, as long as we're not too
        # behind on processing
        self.imu_data_packets = self.imu.get_imu_data_packets()

        # This should not happen, since we wait for IMU packets.
        if not self.imu_data_packets:
            return

        # Split the data packets into estimated and raw data packets for use in processing and
        # logging
        self.est_data_packets = [
            data_packet
            for data_packet in self.imu_data_packets
            if type(data_packet) is EstimatedDataPacket  # type() is ~55% faster than isinstance()
        ]

        # Update the processed data with the new data packets. We only care about EstDataPackets
        self.data_processor.update(self.est_data_packets)

        # Get the processor data packets from the data processor, this will have the same length
        # as the number of EstimatedDataPackets in data_packets
        if self.est_data_packets:
            self.processor_data_packets = self.data_processor.get_processor_data_packets()

        # Gets the apogee predictor packets
        self.apogee_predictor_data_packets = self.apogee_predictor.get_prediction_data_packets()

        # Update the last apogee predictor packet
        if self.apogee_predictor_data_packets:
            self.last_apogee_predictor_packet = self.apogee_predictor_data_packets[-1]

        # Update the state machine based on the latest processed data
        self.state.update()

        # Create packets representing the current state of the airbrakes system:
        self.generate_data_packets()

        # Logs the current state, extension, IMU data, and processed data
        self.logger.log(
            self.context_data_packet,
            self.servo_data_packet,
            self.imu_data_packets,
            self.processor_data_packets,
            self.apogee_predictor_data_packets,
        )

    def extend_airbrakes(self) -> None:
        """
        Extends the airbrakes to the maximum extension.
        """
        self.servo.set_extended()

    def retract_airbrakes(self) -> None:
        """
        Retracts the airbrakes to the minimum extension.
        """
        self.servo.set_retracted()

    def predict_apogee(self) -> None:
        """
        Predicts the apogee of the rocket based on the current processed data. This
        should only be called in the coast state, before we start controlling the airbrakes.
        """
        # We have to only run this for estimated data packets, otherwise we send duplicate
        # data to the predictor (because for a raw data packet, we still have the 'old'
        # processor_data_packets)
        # This would result in a very slow convergence and inaccurate predictions.
        if self.est_data_packets:
            self.apogee_predictor.update(self.processor_data_packets)

    def generate_data_packets(self) -> None:
        """
        Generates the context data packet and servo data packet to be logged.
        """
        # Create a context data packet to log the current state of the airbrakes system
        self.context_data_packet = ContextDataPacket(
            state_letter=self.state.name[0],
            fetched_packets_in_main=len(self.imu_data_packets),
            imu_queue_size=self.imu.queue_size,
            apogee_predictor_queue_size=self.apogee_predictor.processor_data_packet_queue_size,
            fetched_imu_packets=self.imu.fetched_imu_packets,
            update_timestamp_ns=time.time_ns(),
        )

        # Creates a servo data packet to log the current state of the servo
        self.servo_data_packet = ServoDataPacket(
            set_extension=str(self.servo.current_extension.value),
            encoder_position=str(self.servo.get_encoder_reading()),
        )
