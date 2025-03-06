"""Module which provides a high level interface to the air brakes system on the rocket."""

import time
from typing import TYPE_CHECKING

from airbrakes.constants import MAIN_PROCESS_PRIORITY
from airbrakes.hardware.camera import Camera
from airbrakes.interfaces.base_imu import BaseIMU
from airbrakes.interfaces.base_servo import BaseServo
from airbrakes.state import StandbyState, State
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import DataProcessor
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
    Manages the state machine for the rocket's air brakes system, keeping track of the current state
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
        servo: BaseServo,
        imu: BaseIMU,
        camera: Camera,
        logger: Logger,
        data_processor: DataProcessor,
        apogee_predictor: ApogeePredictor,
    ) -> None:
        """
        Initializes AirbrakesContext with the specified hardware objects, Logger, IMUDataProcessor,
        and ApogeePredictor. The state machine starts in StandbyState, which is the initial
        state of the air brakes system.
        :param servo: The servo object that controls the extension of the air brakes. This can be a
        real servo or a mocked servo.
        :param imu: The IMU object that reads data from the rocket's IMU. This can be a real IMU,
        mock IMU, or simulation IMU.
        :param camera: The camera object that records video from the rocket. This can be a real
        camera or a mock camera.
        :param logger: The logger object that logs data to a CSV file. This can be a real logger or
        a mock logger.
        :param data_processor: The IMUDataProcessor object that processes IMU data on a higher
        level.
        :param apogee_predictor: The apogee predictor object that predicts the apogee of the rocket.
        """
        self.servo: BaseServo = servo
        self.imu: BaseIMU = imu
        self.camera: Camera = camera
        self.logger: Logger = logger
        self.data_processor: DataProcessor = data_processor
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
        Starts the processes for the IMU, Logger, ApogeePredictor, and Camera. This is called
        before the main loop starts.
        """
        set_process_priority(MAIN_PROCESS_PRIORITY)  # Higher than normal priority
        self.imu.start()
        self.logger.start()
        self.apogee_predictor.start()
        # Currently there is no camera for the airbrakes, but we will leave this here for future
        # use
        # self.camera.start()

    def stop(self) -> None:
        """
        Handles shutting down the air brakes system. This will cause the main loop to break. It
        retracts the air brakes and stops the processes for IMU, Logger, ApogeePredictor and Camera.
        """
        if self.shutdown_requested:
            return
        self.retract_airbrakes()
        self.imu.stop()
        self.logger.stop()
        self.apogee_predictor.stop()
        # self.camera.stop()
        self.shutdown_requested = True

    def update(self) -> None:
        """
        Called every loop iteration from the main process. Depending on the current state, it will
        do different things. It is what controls the air brakes and chooses when to move to the next
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
        # logging.
        self.est_data_packets: list[EstimatedDataPacket] = [  # type: ignore
            data_packet
            for data_packet in self.imu_data_packets
            if type(data_packet) is EstimatedDataPacket  # type() is ~55% faster than isinstance()
        ]

        # Update the data processor with the new data packets.
        self.data_processor.update(self.est_data_packets)

        # Get the Processor Data Packets from the data processor, this will have the same length
        # as the number of EstimatedDataPackets in data_packets
        if self.est_data_packets:
            self.processor_data_packets = self.data_processor.get_processor_data_packets()

        # Gets the Apogee Predictor Data Packets
        self.apogee_predictor_data_packets = self.apogee_predictor.get_prediction_data_packets()

        # Update the last Apogee Predictor Data Packet
        if self.apogee_predictor_data_packets:
            self.last_apogee_predictor_packet = self.apogee_predictor_data_packets[-1]

        # Update the state machine based on the latest processed data
        self.state.update()

        # Create Context Data Packets representing the current state of the air brakes system:
        self.generate_data_packets()

        # Logs all of the packet types from each of the relevant processes
        self.logger.log(
            self.context_data_packet,
            self.servo_data_packet,
            self.imu_data_packets,
            self.processor_data_packets,
            self.apogee_predictor_data_packets,
        )

    def generate_data_packets(self) -> None:
        """
        Generates the Context Data Packet and Servo Data Packet to be logged.
        """
        # Create a Context Data Packet to log the current state and queue information of the
        # Airbrakes program.
        self.context_data_packet = ContextDataPacket(
            state_letter=self.state.name[0],
            retrieved_imu_packets=len(self.imu_data_packets),
            queued_imu_packets=self.imu.queued_imu_packets,
            apogee_predictor_queue_size=self.apogee_predictor.processor_data_packet_queue_size,
            imu_packets_per_cycle=self.imu.imu_packets_per_cycle,
            update_timestamp_ns=time.time_ns(),
        )

        # Creates a Servo Data Packet to log the current extension of the servo and the position
        # of the encoder.
        self.servo_data_packet = ServoDataPacket(
            set_extension=str(self.servo.current_extension.value),
            encoder_position=self.servo.get_encoder_reading(),
        )

    def extend_airbrakes(self) -> None:
        """
        Extends the air brakes to the maximum extension.
        """
        self.data_processor.prepare_for_extending_airbrakes()
        self.servo.set_extended()

    def retract_airbrakes(self) -> None:
        """
        Retracts the air brakes to the minimum extension.
        """
        self.servo.set_retracted()

    def switch_altitude_back_to_pressure(self) -> None:
        """
        Switches the altitude back to pressure, after airbrakes have been retracted.
        """
        # This isn't in retract_airbrakes because we only want to call this after the airbrakes
        # have been extended. We call retract_airbrakes at the beginning of every state, so we don't
        # want this to be called every time.
        self.data_processor.prepare_for_retracting_airbrakes()

    def start_velocity_calibration(self) -> None:
        """
        Because we integrate for velocity, error can accumulate. This function starts the
        calibration process for velocity.
        """
        self.data_processor.start_storing_altitude_data()

    def predict_apogee(self) -> None:
        """
        Predicts the apogee of the rocket based on the current processed data. This
        should only be called in the coast state, before we start controlling the air brakes.
        """
        # Because the IMUDataProcessor only uses Estimated Data Packets to create Processor Data
        # Packets, we only update the apogee predictor when Estimated Data Packets are ready.
        if self.est_data_packets:
            self.apogee_predictor.update(self.processor_data_packets)
