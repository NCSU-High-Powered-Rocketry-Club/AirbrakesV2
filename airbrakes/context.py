"""Module which provides a high level interface to the airbrakes system on the rocket."""

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
    """
    Manages the state machine for the rocket's air brakes system, keeping
    track of the current state and communicating with hardware like the servo
    and IMU. This class is what connects the state machine to the hardware.

    Read more about the state machine pattern here:
    https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

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
        """
        Initializes Context with the specified hardware objects, Logger,
        DataProcessor, and ApogeePredictor.

        The state machine starts in StandbyState, which is the initial
        state of the air brakes system.
        :param servo: The servo object that controls the extension of
            the air brakes. This can be a real servo or a mocked servo.
        :param imu: The IMU object that reads data from the rocket's
            IMU device. This can be a real IMU or mock IMU.
        :param logger: The logger object that logs data to a CSV file.
            This can be a real logger or a mock logger.
        :param data_processor: The DataProcessor object that processes
            IMU data on a higher level.
        :param apogee_predictor: The ApogeePredictor object that
            predicts what the apogee of the rocket will be based on the
            processed data.
        """
        self.servo = servo
        self.imu = imu
        self.logger = logger
        self.data_processor = data_processor
        self.apogee_predictor = apogee_predictor
        # The rocket starts in the StandbyState.
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
        """
        Starts the threads for the IMU device, Logger, and ApogeePredictor.

        This is called before the main loop starts.

        :param wait_for_start: If True, waits for all the threads to
            have actually started. This matters because starting threads
            via the "spawn"/"forkserver" method is slow, and we want to
            prevent data races where the main loop tries to access data
            before the threads have started.
        """
        self.imu.start()
        self.logger.start()
        self.apogee_predictor.start()
        self.servo.start()
        self.servo.retract_airbrakes()

        if wait_for_start:
            # Wait for all threads to start. It is assumed that once IMU is running, all other
            # threads are also running. Even if they aren't it's okay, since the queue will fill
            # up with data and the other threads will start when they wake up.
            while not self.imu.is_running:
                time.sleep(BUSY_WAIT_SECONDS)

    def stop(self) -> None:
        """
        Handles shutting down the air brakes system.

        This will cause the main loop to break. It retracts the air
        brakes and stops the processes for the IMU device, Logger, and
        ApogeePredictor.
        """
        if self.shutdown_requested:
            return
        self.shutdown_requested = True
        self.retract_airbrakes()
        self.imu.stop()
        self.logger.stop()
        self.apogee_predictor.stop()
        self.servo.stop()

    def update(self) -> None:
        """
        Called every loop iteration from the main thread. This is
        essentially the "brain" of the air brakes system, where all the data is
        collected, processed, and logged, and the state machine is updated.

        This function retrieves the latest IMU data packets, processes
        them, updates the state machine, generates data packets for
        logging, and logs all relevant data.
        """
        self.imu_data_packets = self.imu.get_imu_data_packets()
        if not self.imu_data_packets:
            return

        # Filter the IMU data packets to keep only estimated data packets.
        self.est_data_packets = [
            packet for packet in self.imu_data_packets if isinstance(packet, EstimatedDataPacket)
        ]

        # Update the data processor with the new estimated data packets.
        self.data_processor.update(self.est_data_packets)

        # Gets the processor data packets generated by the data processor.
        # One processor data packet is created for each estimated data packet.
        # TODO: Determine whether processor_data_packets should be cleared when no new estimated
        # data packets are available to prevent apogee prediction from using stale processor data.
        # self.processor_data_packets = []
        if self.est_data_packets:
            self.processor_data_packets = self.data_processor.get_processor_data_packets()

        # Gets the most recent Apogee Predictor Data Packets, this will only have new data if we are
        # in coast and have called predict_apogee(), and the apogee predictor has had time to
        # process the data and predict the apogee.
        apogee_prediction_packet = self.apogee_predictor.get_prediction_data_packet()
        if apogee_prediction_packet:
            self.most_recent_apogee_predictor_data_packet = apogee_prediction_packet

        # Update the state machine based on the latest processed data
        self.state.update()

        # Create context Data Packets representing the current state of the air brakes system:
        self.generate_data_packets()

        # This if statement is just because of an IDE issue, it's not possible for them to be
        # None here
        if self.context_data_packet is not None and self.servo_data_packet is not None:
            # Logs all the packet types from each of the relevant processes.
            self.logger.log(
                self.context_data_packet,
                self.servo_data_packet,
                self.imu_data_packets,
                self.processor_data_packets,
                self.most_recent_apogee_predictor_data_packet,
            )

    def extend_airbrakes(self, velocity: float) -> None:
        """Extends the air brakes based on the rocket's current velocity."""
        self.data_processor.prepare_for_extending_airbrakes()
        self.servo.extend_airbrakes(velocity)

    def retract_airbrakes(self) -> None:
        """Retracts the air brakes to the minimum extension."""
        # We don't want to retract the airbrakes if they are already retracted, so we check if the 
        # servo is
        if abs(self.servo.servo_extension - SERVO_MIN_EXTENSION) > SERVO_EXTENSION_TOLERANCE:
            self.data_processor.prepare_for_retracting_airbrakes()
            self.servo.retract_airbrakes()

    def predict_apogee(self) -> None:
        """
        Predicts the apogee of the rocket based on the current processed
        data.

        This should only be called in the coast state, before we start
        controlling the air brakes.
        """
        # TODO: see if we should change this to processed_data_packets
        if self.est_data_packets:
            # We pass in the most recent IMU Data Packet to the apogee predictor.
            self.apogee_predictor.update(self.processor_data_packets[-1])

    def generate_data_packets(self) -> None:
        """
        Generates the Context Data Packet and Servo Data Packet to be
        logged.
        """
        # Create a Context Data Packet to log the current state and queue information of the
        # Airbrakes program.
        self.context_data_packet = ContextDataPacket(
            state=type(self.state),
            retrieved_imu_packets=len(self.imu_data_packets),
            queued_imu_packets=self.imu.queued_imu_packets,
            imu_packets_per_cycle=self.imu.imu_packets_per_cycle,
            apogee_predictor_queue_size=self.apogee_predictor.processor_data_packet_queue_size,
            update_timestamp_ns=time.time_ns(),
        )
        self.servo_data_packet = self.servo.get_servo_data_packet()
