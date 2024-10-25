"""Module which provides a high level interface to the air brakes system on the rocket."""

from typing import TYPE_CHECKING

from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.logger import Logger
from airbrakes.hardware.imu import IMU, IMUDataPacket
from airbrakes.hardware.servo import Servo
from airbrakes.state import StandByState, State, CoastState
from constants import ServoExtension

if TYPE_CHECKING:
    from collections import deque

    from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket


class AirbrakesContext:
    """
    Manages the state machine for the rocket's airbrakes system, keeping track of the current state and communicating
    with hardware like the servo and IMU. This class is what connects the state machine to the hardware.

    Read more about the state machine pattern here: https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

    __slots__ = (
        "apogee_predictor",
        "current_extension",
        "data_processor",
        "imu",
        "logger",
        "servo",
        "shutdown_requested",
        "state",
    )

    def __init__(self, servo: Servo, imu: IMU, logger: Logger, data_processor: IMUDataProcessor) -> None:
        """
        Initializes the airbrakes context with the specified hardware objects, logger, and data processor. The state
        machine starts in the StandByState, which is the initial state of the airbrakes system.
        :param servo: The servo object that controls the extension of the airbrakes. This can be a real servo or a mock
        servo.
        :param imu: The IMU object that reads data from the rocket's IMU. This can be a real IMU or a mock IMU.
        :param logger: The logger object that logs data to a CSV file.
        :param data_processor: The data processor object that processes IMU data on a higher level.
        """
        self.servo = servo
        self.imu = imu
        self.logger = logger
        self.data_processor = data_processor

        # Placeholder for the current airbrake extension until they are set
        self.current_extension: ServoExtension = ServoExtension.MIN_EXTENSION

        self.state: State = StandByState(self)
        self.apogee_predictor: ApogeePredictor = ApogeePredictor()
        self.shutdown_requested = False

    def start(self) -> None:
        """
        Starts the IMU and logger processes. This is called before the main while loop starts.
        """
        self.imu.start()
        self.logger.start()
        self.apogee_predictor.start()

    def stop(self) -> None:
        """
        Handles shutting down the airbrakes. This will cause the main loop to break. It retracts the airbrakes, stops
        the IMU, and stops the logger.
        """
        self.retract_airbrakes()
        self.imu.stop()
        self.logger.stop()
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
        imu_data_packets: deque[IMUDataPacket] = self.imu.get_imu_data_packets()

        # This should never happen, but if it does, we want to not error out and wait for packets
        if not imu_data_packets:
            return

        # Split the data packets into estimated and raw data packets for use in processing and logging
        est_data_packets = [
            data_packet
            for data_packet in imu_data_packets.copy()
            if isinstance(data_packet, EstimatedDataPacket)
            # The copy() above is critical to ensure the data here is not modified by the data processor
        ]

        # Update the processed data with the new data packets. We only care about EstimatedDataPackets
        self.data_processor.update(est_data_packets)

        # Get the processed data packets from the data processor, this will have the same length as the number of
        # EstimatedDataPackets in data_packets
        processed_data_packets: deque[ProcessedDataPacket] = self.data_processor.get_processed_data_packets()

        if self.state.name[0] == "C":  # Only run apogee prediction in coast state:
            # pass
            self.apogee_predictor.update(processed_data_packets)
        elif self.state.name[0] == "F":  # Stop apogee prediction process in free fall:
            self.apogee_predictor.stop()
        # Update the state machine based on the latest processed data
        self.state.update()

        # Logs the current state, extension, IMU data, and processed data
        self.logger.log(self.state.name[0], self.current_extension.value, imu_data_packets, processed_data_packets)

    def extend_airbrakes(self) -> None:
        """
        Extends the airbrakes to the maximum extension.
        """
        self.servo.set_extended()
        self.current_extension = ServoExtension.MAX_EXTENSION

    def retract_airbrakes(self) -> None:
        """
        Retracts the airbrakes to the minimum extension.
        """
        self.servo.set_retracted()
        self.current_extension = ServoExtension.MIN_EXTENSION
