"""
Module which provides a high level interface to the air brakes system on the rocket.
"""

import time
from typing import TYPE_CHECKING

from airbrakes.constants import BUSY_WAIT_SECONDS
from airbrakes.state import StandbyState, State
from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket
from airbrakes.telemetry.packets.servo_data_packet import ServoDataPacket
from airbrakes.utils import convert_ns_to_s

if TYPE_CHECKING:
    from airbrakes.hardware.imu import IMUDataPacket
    from airbrakes.interfaces.base_imu import BaseIMU
    from airbrakes.interfaces.base_servo import BaseServo
    from airbrakes.telemetry.apogee_predictor import ApogeePredictor
    from airbrakes.telemetry.data_processor import DataProcessor
    from airbrakes.telemetry.logger import Logger
    from airbrakes.telemetry.packets.apogee_predictor_data_packet import (
        ApogeePredictorDataPacket,
    )
    from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket


class Context:
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
        "context_data_packet",
        "convergence_height",
        "convergence_time",
        "data_processor",
        "est_data_packets",
        "first_converged_apogee",
        "imu",
        "imu_data_packets",
        "launch_time_ns",
        "logger",
        "most_recent_apogee_predictor_packet",
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
        Initializes AirbrakesContext with the specified hardware objects, Logger, DataProcessor, and
        ApogeePredictor.

        The state machine starts in StandbyState, which is the initial state of the air brakes
        system.
        :param servo: The servo object that controls the extension of the air brakes. This can be a
            real servo or a mocked servo.
        :param imu: The IMU object that reads data from the rocket's IMU. This can be a real IMU,
            mock IMU, or simulation IMU.
        :param logger: The logger object that logs data to a CSV file. This can be a real logger or
            a mock logger.
        :param data_processor: The DataProcessor object that processes IMU data on a higher level.
        :param apogee_predictor: The ApogeePredictor object that predicts what the apogee of the
            rocket will be based on the processed data.
        """
        self.servo: BaseServo = servo
        self.imu: BaseIMU = imu
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
        self.most_recent_apogee_predictor_packet: ApogeePredictorDataPacket | None = None

        # The first apogee prediction packet with a valid prediction, used mostly for the display
        self.first_converged_apogee: float | None = None
        self.convergence_time: float | None = None
        self.convergence_height: float | None = None

        # Keeps track of the launch time, used for calculating convergence time
        self.launch_time_ns: int = 0

    def start(self, wait_for_start: bool = False) -> None:
        """
        Starts the threads for the IMU, Logger, and ApogeePredictor.

        This is called before the main loop starts.

        :param wait_for_start: If True, waits for all the threads to have actually started. This
            matters because starting threads via the "spawn"/"forkserver" method is slow, and we
            want to prevent data races where the main loop tries to access data before the threads
            have started.
        """
        self.imu.start()
        self.logger.start()
        self.apogee_predictor.start()

        if wait_for_start:
            # Wait for all processes to start. It is assumed that once the IMU is running, all other
            # processes are also running. Even if they aren't it's okay, since the queue will fill
            # up with data and the other processes will start processing it when they wake up.
            while not self.imu.is_running:
                time.sleep(BUSY_WAIT_SECONDS)

    def stop(self) -> None:
        """
        Handles shutting down the air brakes system.

        This will cause the main loop to break. It retracts the air brakes and stops the processes
        for IMU, Logger, and ApogeePredictor.
        """
        if self.shutdown_requested:
            return
        self.shutdown_requested = True
        self.retract_airbrakes()
        self.imu.stop()
        self.logger.stop()
        self.apogee_predictor.stop()

    def update(self) -> None:
        """
        Called every loop iteration from the main thread. This is essentially the "brain" of the
        air brakes system, where all the data is collected, processed, and logged, and the state
        machine is updated.

        This function retrieves the latest IMU data packets, processes them, updates the state
        machine, generates data packets for logging, and logs all relevant data.
        """
        # get_imu_data_packets() gets from the "first" item in the queue, i.e, the set of data
        # *may* not be the most recent data. But we want continuous data for state, apogee,
        # and logging purposes, so we don't need to worry about that, as long as we're not too
        # behind on processing
        self.imu_data_packets = self.imu.get_imu_data_packets()

        # This should not happen generally, since we wait for IMU packets. Only happens at the end
        # of the flight in a mock replay.
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
        # as the number of EstimatedDataPackets in data_packets because a processor data packet is
        # created for each estimated data packet.
        if self.est_data_packets:
            self.processor_data_packets = self.data_processor.get_processor_data_packets()

        # Gets the Apogee Predictor Data Packets, this will only have new data if we are in
        # coast and have called predict_apogee(), and the apogee predictor has had time to process
        # the data and predict the apogee.
        self.apogee_predictor_data_packets = self.apogee_predictor.get_prediction_data_packets()

        # Update the first and most recent Apogee Predictor Data Packet
        if self.apogee_predictor_data_packets:
            self._set_apogee_prediction_data()

        # Update the state machine based on the latest processed data
        self.state.update()

        # Create Context Data Packets representing the current state of the air brakes system:
        self.generate_data_packets()

        # Logs all the packet types from each of the relevant processes
        self.logger.log(
            self.context_data_packet,
            self.servo_data_packet,
            self.imu_data_packets,
            self.processor_data_packets,
            self.apogee_predictor_data_packets,
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

    def predict_apogee(self) -> None:
        """
        Predicts the apogee of the rocket based on the current processed data.

        This should only be called in the coast state, before we start controlling the air brakes.
        """
        # Because the DataProcessor only uses Estimated Data Packets to create Processor Data
        # Packets, we only update the apogee predictor when Estimated Data Packets are ready.
        if self.est_data_packets:
            self.apogee_predictor.update(self.processor_data_packets)

    def generate_data_packets(self) -> None:
        """
        Generates the Context Data Packet and Servo Data Packet to be logged.
        """
        # Create a Context Data Packet to log the current state and queue information of the
        # Airbrakes program.
        self.context_data_packet = ContextDataPacket(
            state=type(self.state),
            retrieved_imu_packets=len(self.imu_data_packets),
            queued_imu_packets=self.imu.queued_imu_packets,
            apogee_predictor_queue_size=self.apogee_predictor.processor_data_packet_queue_size,
            imu_packets_per_cycle=self.imu.imu_packets_per_cycle,
            update_timestamp_ns=time.time_ns(),
        )

        # Creates a Servo Data Packet to log the current extension of the servo and the position
        # of the encoder.
        self.servo_data_packet = ServoDataPacket(
            set_extension=self.servo.current_extension,
            encoder_position=self.servo.get_encoder_reading(),
        )

    def _set_apogee_prediction_data(self) -> None:
        """
        Sets the last and first apogee prediction data packets.

        This is called every loop iteration if there are new apogee predictor data packets.
        """
        self.most_recent_apogee_predictor_packet = self.apogee_predictor_data_packets[-1]

        # Set the first apogee prediction packet if it hasn't been set yet, and only if we have a
        # converged valid prediction.
        if (
            self.first_converged_apogee is None
            and self.most_recent_apogee_predictor_packet.predicted_apogee > 0
        ):
            self.first_converged_apogee = self.most_recent_apogee_predictor_packet.predicted_apogee
            self.convergence_time = convert_ns_to_s(self.state.start_time_ns - self.launch_time_ns)
            self.convergence_height = self.processor_data_packets[-1].current_altitude
