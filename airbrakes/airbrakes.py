"""Module which provides a high level interface to the air brakes system on the rocket."""

from collections import deque
from typing import TYPE_CHECKING

from airbrakes.constants import ServoExtension
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.logger import Logger
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket
from airbrakes.hardware.imu import IMU
from airbrakes.hardware.servo import Servo
from airbrakes.state import StandbyState, State

if TYPE_CHECKING:
    from airbrakes.data_handling.packets.context_data_packet import ContextPacket
    from airbrakes.data_handling.packets.processor_data_packet import ProcessedDataPacket
    from airbrakes.hardware.imu import IMUDataPacket


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
        "current_extension",
        "data_processor",
        "debug_packet",
        "est_data_packets",
        "imu",
        "imu_data_packets",
        "logger",
        "processed_data_packets",
        "servo",
        "shutdown_requested",
        "state",
    )

    def __init__(
        self,
        servo: Servo,
        imu: IMU,
        logger: Logger,
        data_processor: IMUDataProcessor,
        apogee_predictor: ApogeePredictor,
    ) -> None:
        """
        Initializes the airbrakes context with the specified hardware objects, logger, and data
        processor. The state machine starts in the StandbyState, which is the initial state of the
        airbrakes system.
        :param servo: The servo object that controls the extension of the airbrakes. This can be a
        real servo or a mock servo.
        :param imu: The IMU object that reads data from the rocket's IMU. This can be a real IMU or
        a mock IMU.
        :param logger: The logger object that logs data to a CSV file.
        :param data_processor: The data processor object that processes IMU data on a higher level.
        :param apogee_predictor: The apogee predictor object that predicts the apogee of the rocket.
        """
        self.servo: Servo = servo
        self.imu: IMU = imu
        self.logger: Logger = logger
        self.data_processor: IMUDataProcessor = data_processor
        self.apogee_predictor: ApogeePredictor = apogee_predictor

        # Placeholder for the current airbrake extension until they are set
        self.current_extension: ServoExtension = ServoExtension.MIN_EXTENSION
        # The rocket starts in the StandbyState
        self.state: State = StandbyState(self)
        self.shutdown_requested = False
        self.imu_data_packets: deque[IMUDataPacket] = deque()
        self.processed_data_packets: list[ProcessedDataPacket] = []
        self.est_data_packets: list[EstimatedDataPacket] = []
        self.debug_packet: ContextPacket | None = None

    def start(self) -> None:
        """
        Starts the IMU and logger processes. This is called before the main while loop starts.
        """
        self.imu.start()
        self.logger.start()
        self.apogee_predictor.start()

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

        # This happens quite often, on our PC's since they are much faster than the Pi.
        if not self.imu_data_packets:
            return

        # Split the data packets into estimated and raw data packets for use in processing and
        # logging
        self.est_data_packets = [
            data_packet
            for data_packet in self.imu_data_packets
            if isinstance(data_packet, EstimatedDataPacket)
        ]

        # Update the processed data with the new data packets. We only care about EstDataPackets
        self.data_processor.update(self.est_data_packets)

        # Get the processed data packets from the data processor, this will have the same length
        # as the number of EstimatedDataPackets in data_packets
        if self.est_data_packets:
            self.processed_data_packets = self.data_processor.get_processed_data_packets()

        # Update the state machine based on the latest processed data
        self.state.update()

        # Gets what we have currently set the extension of the airbrakes to
        self.current_extension = self.servo.current_extension

        # Logs the current state, extension, IMU data, and processed data
        self.logger.log(
            self.state.name,
            self.current_extension.value,
            self.imu_data_packets,
            self.processed_data_packets,
            self.debug_packet,
        )

    def extend_airbrakes(self) -> None:
        """
        Extends the airbrakes to the maximum extension.
        """
        self.servo.set_extended()
        self.current_extension = self.servo.current_extension

    def retract_airbrakes(self) -> None:
        """
        Retracts the airbrakes to the minimum extension.
        """
        self.servo.set_retracted()
        self.current_extension = self.servo.current_extension

    def predict_apogee(self) -> None:
        """
        Predicts the apogee of the rocket based on the current processed data. This
        should only be called in the coast state, before we start controlling the airbrakes.
        """
        # We have to only run this for estimated data packets, otherwise we send duplicate
        # data to the predictor (because for a raw data packet, we still have the 'old'
        # processed_data_packets)
        # This would result in a very slow convergence and inaccurate predictions.
        if self.est_data_packets:
            self.apogee_predictor.update(self.processed_data_packets)
