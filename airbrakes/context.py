"""
Module which provides a high level interface to the air brakes system on the
rocket.
"""

import time
from typing import TYPE_CHECKING

from airbrakes.constants import BUSY_WAIT_SECONDS
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket
from airbrakes.state import StandbyState, State

if TYPE_CHECKING:
    from firm_client import FIRMDataPacket

    from airbrakes.base_classes.base_firm import BaseFIRM
    from airbrakes.base_classes.base_servo import BaseServo
    from airbrakes.data_handling.apogee_predictor import ApogeePredictor
    from airbrakes.data_handling.data_processor import DataProcessor
    from airbrakes.data_handling.logger import Logger
    from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
        ApogeePredictorDataPacket,
    )


class Context:
    """
    Manages the state machine for the rocket's air brakes system, keeping
    track of the current state and communicating with hardware like the servo
    and FIRM. This class is what connects the state machine to the hardware.

    Read more about the state machine pattern here:
    https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

    __slots__ = (
        "apogee_predictor",
        "context_data_packet",
        "data_processor",
        "firm",
        "firm_data_packets",
        "launch_time_seconds",
        "logger",
        "most_recent_apogee_predictor_data_packet",
        "servo",
        "servo_data_packet",
        "shutdown_requested",
        "state",
    )

    def __init__(
        self,
        servo: BaseServo,
        firm: BaseFIRM,
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
        :param firm: The FIRM object that reads data from the rocket's
            FIRM device. This can be a real FIRM or mock FIRM.
        :param logger: The logger object that logs data to a CSV file.
            This can be a real logger or a mock logger.
        :param data_processor: The DataProcessor object that processes
            FIRM data on a higher level.
        :param apogee_predictor: The ApogeePredictor object that
            predicts what the apogee of the rocket will be based on the
            processed data.
        """
        self.servo: BaseServo = servo
        self.firm: BaseFIRM = firm
        self.logger: Logger = logger
        self.data_processor: DataProcessor = data_processor
        self.apogee_predictor: ApogeePredictor = apogee_predictor
        # The rocket starts in the StandbyState
        self.state: State = StandbyState(self)

        self.shutdown_requested = False
        self.firm_data_packets: list[FIRMDataPacket] = []
        self.most_recent_apogee_predictor_data_packet: ApogeePredictorDataPacket | None = None
        self.context_data_packet: ContextDataPacket = None
        self.servo_data_packet: ServoDataPacket = None

        # Keeps track of the launch time, used for calculating convergence time
        self.launch_time_seconds: float = 0

    def start(self, wait_for_start: bool = False) -> None:
        """
        Starts the threads for the FIRM device, Logger, and ApogeePredictor.

        This is called before the main loop starts.

        :param wait_for_start: If True, waits for all the threads to
            have actually started. This matters because starting threads
            via the "spawn"/"forkserver" method is slow, and we want to
            prevent data races where the main loop tries to access data
            before the threads have started.
        """
        self.firm.start()
        self.logger.start()
        self.apogee_predictor.start()

        if wait_for_start:
            # Wait for all processes to start. It is assumed that once FIRM is running, all other
            # processes are also running. Even if they aren't it's okay, since the queue will fill
            # up with data and the other processes will start processing it when they wake up.
            while not self.firm.is_running:
                time.sleep(BUSY_WAIT_SECONDS)

    def stop(self) -> None:
        """
        Handles shutting down the air brakes system.

        This will cause the main loop to break. It retracts the air
        brakes and stops the processes for the FIRM device, Logger, and
        ApogeePredictor.
        """
        if self.shutdown_requested:
            return
        self.shutdown_requested = True
        self.retract_airbrakes()
        self.firm.stop()
        self.logger.stop()
        self.apogee_predictor.stop()

    def update(self) -> None:
        """
        Called every loop iteration from the main thread. This is
        essentially the "brain" of the air brakes system, where all the data is
        collected, processed, and logged, and the state machine is updated.

        This function retrieves the latest FIRM data packets, processes
        them, updates the state machine, generates data packets for
        logging, and logs all relevant data.
        """
        self.firm_data_packets = self.firm.get_data_packets()

        # This should not happen generally, since we wait for FIRM packets. Only happens at the end
        # of the flight in a mock replay.
        if not self.firm_data_packets:
            return

        # Update the data processor with the new data packets.
        self.data_processor.update(self.firm_data_packets)

        # Gets the most recent Apogee Predictor Data Packets, this will only have new data if we are
        # in coast and have called predict_apogee(), and the apogee predictor has had time to
        # process the data and predict the apogee.
        apogee_prediction_packet = self.apogee_predictor.get_prediction_data_packet()
        if apogee_prediction_packet:
            self.most_recent_apogee_predictor_data_packet = apogee_prediction_packet

        # Update the state machine based on the latest processed data
        self.state.update()

        # Create Context Data Packets representing the current state of the air brakes system:
        self.generate_data_packets()

        # Logs all the packet types from each of the relevant processes
        self.logger.log(
            self.context_data_packet,
            self.servo_data_packet,
            self.firm_data_packets,
            self.most_recent_apogee_predictor_data_packet,
        )

    def extend_airbrakes(self) -> None:
        """Extends the air brakes to the maximum extension."""
        self.servo.set_extended()

    def retract_airbrakes(self) -> None:
        """Retracts the air brakes to the minimum extension."""
        self.servo.set_retracted()

    def predict_apogee(self) -> None:
        """
        Predicts the apogee of the rocket based on the current processed
        data.

        This should only be called in the coast state, before we start
        controlling the air brakes.
        """
        if self.firm_data_packets:
            # We pass in the most recent FIRM Data Packet to the apogee predictor
            self.apogee_predictor.update(self.firm_data_packets[-1])

    def generate_data_packets(self) -> None:
        """
        Generates the Context Data Packet and Servo Data Packet to be
        logged.
        """
        # Create a Context Data Packet to log the current state and queue information of the
        # Airbrakes program.
        self.context_data_packet = ContextDataPacket(
            state=type(self.state),
            retrieved_firm_packets=len(self.firm_data_packets),
            apogee_predictor_queue_size=self.apogee_predictor.firm_data_packet_queue_size,
            update_timestamp_ns=time.time_ns(),
        )

        # Creates a Servo Data Packet to log the current extension of the servo and the position
        # of the encoder.
        self.servo_data_packet = ServoDataPacket(
            set_extension=self.servo.current_extension,
            encoder_position=self.servo.get_encoder_reading(),
            battery_voltage=f"{self.servo.get_battery_volts()}",
            current_milliamps=f"{self.servo.get_system_current_milliamps()}",
        )
