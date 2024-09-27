"""Module which provides a high level interface to the air brakes system on the rocket."""

import collections

from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from airbrakes.data_handling.logger import Logger
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from airbrakes.hardware.imu import IMU, IMUDataPacket
from airbrakes.hardware.servo import Servo
from airbrakes.state import StandByState, State


class AirbrakesContext:
    """
    Manages the state machine for the rocket's airbrakes system, keeping track of the current state and communicating
    with hardware like the servo and IMU. This class is what connects the state machine to the hardware.

    Read more about the state machine pattern here: https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

    __slots__ = (
        "current_extension",
        "data_processor",
        "imu",
        "logger",
        "servo",
        "shutdown_requested",
        "state",
    )

    def __init__(self, servo: Servo, imu: IMU, logger: Logger, data_processor: IMUDataProcessor):
        self.servo = servo
        self.imu = imu
        self.logger = logger
        self.data_processor = data_processor

        self.state: State = StandByState(self)
        self.shutdown_requested = False

        # Placeholder for the current airbrake extension until they are set
        self.current_extension: float = 0.0

    def start(self) -> None:
        """
        Starts the IMU and logger processes. This is called before the main while loop starts.
        """
        self.imu.start()
        self.logger.start()

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
        data_packets: collections.deque[IMUDataPacket] = self.imu.get_imu_data_packets()

        # This should never happen, but if it does, we want to not error out and wait for packets
        if not data_packets:
            return

        # Split the data packets into estimated and raw data packets for use in processing and logging
        est_data_packets = [
            data_packet for data_packet in data_packets.copy() if isinstance(data_packet, EstimatedDataPacket)
        ]
        raw_data_packets = [
            data_packet for data_packet in data_packets.copy() if isinstance(data_packet, RawDataPacket)
        ]

        # Update the processed data with the new data packets. We only care about EstimatedDataPackets
        self.data_processor.update_data(est_data_packets)

        # Get the processed data packets from the data processor, this will have the same length as the number of
        # EstimatedDataPackets in data_packets
        processed_data_packets: list[ProcessedDataPacket] = self.data_processor.get_processed_data()

        # Update the state machine based on the latest processed data
        self.state.update()

        logged_data_packets: collections.deque[LoggedDataPacket] = collections.deque()

        # Makes a logged data packet for every imu data packet (raw or est), and sets the state and extension for it
        # Then, if the imu data packet is an estimated data packet, it adds the data from the corresponding processed
        # data packet
        for packet in raw_data_packets + processed_data_packets:
            is_processed_data_packet = isinstance(packet, ProcessedDataPacket)
            imu_data_packet: IMUDataPacket = packet.estimated_data_packet if is_processed_data_packet else packet

            # Prepare logged data packets:
            # We will only log the first letter of the state name, hence the [0] (to reduce file size)
            logged_data_packet = LoggedDataPacket(
                state=self.state.name[0], extension=self.current_extension, timestamp=imu_data_packet.timestamp
            )

            # Sets attributes for both RawDataPackets and EstimatedDataPackets:
            logged_data_packet.set_imu_data_packet_attributes(imu_data_packet)

            # Prepare logged processed data packets:
            if is_processed_data_packet:
                logged_data_packet.set_processed_data_packet_attributes(packet)

            logged_data_packets.append(logged_data_packet)

        # Logs the current state, extension, IMU data, and processed data
        self.logger.log(logged_data_packets)

    def set_airbrake_extension(self, extension: float) -> None:
        """
        Sets the airbrake extension via the servo. It will be called by the states.
        :param extension: the extension of the airbrakes, between 0 and 1
        """
        self.servo.set_extension(extension)
        self.current_extension = extension

    def stop(self) -> None:
        """
        Handles shutting down the airbrakes. This will cause the main loop to break.
        """
        self.set_airbrake_extension(0.0)
        self.imu.stop()
        self.logger.stop()
        self.shutdown_requested = True
