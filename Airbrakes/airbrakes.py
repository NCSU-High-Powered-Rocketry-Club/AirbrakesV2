"""Module which provides a high level interface to the air brakes system on the rocket."""

from typing import TYPE_CHECKING

from Airbrakes.imu import IMU, IMUDataPacket, RollingAverages
from Airbrakes.logger import Logger
from Airbrakes.servo import Servo
from Airbrakes.state import StandByState, State

if TYPE_CHECKING:
    import collections


class AirbrakesContext:
    """
    Manages the state machine for the rocket's airbrakes system, keeping track of the current state and communicating
    with hardware like the servo and IMU. This class is what connects the state machine to the hardware.

    Read more about the state machine pattern here: https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

    __slots__ = (
        "current_extension",
        "current_imu_data",
        "imu",
        "logger",
        "servo",
        "shutdown_requested",
        "state",
    )

    def __init__(self, logger: Logger, servo: Servo, imu: IMU):
        self.logger = logger
        self.servo = servo
        self.imu = imu

        self.state: State = StandByState(self)
        self.shutdown_requested = False

        # Placeholder for the current airbrake extension and IMU data until they are set
        self.current_extension = 0.0
        self.current_imu_data = IMUDataPacket(0.0)

    def update(self):
        """
        Called every loop iteration from the main process. Depending on the current state, it will
        do different things. It is what controls the airbrakes and chooses when to move to the next
        state.
        """
        # Gets the current extension and IMU data, the states will use these values
        self.current_extension = self.servo.current_extension

        # Let's get 50 data packets to ensure we have enough data to work with.
        # 50 is an arbitrary number for now - if the time resolution between each data packet is
        # 2ms, then we have 2*50 = 100ms of data to work with at once.
        # get_imu_data_packets() gets from the "first" item in the queue, i.e, the set of data
        # *may* not be the most recent data. But we want continous data for proper state and
        # apogee calculation, so we don't need to worry about that, as long as we're not too
        # behind on processing
        data_packets: collections.deque[IMUDataPacket] = self.imu.get_imu_data_packets()

        # Logs the current state, extension, and IMU data
        rolling_average = RollingAverages(data_packets.copy())
        # TODO: Compute state(s) for given IMU data
        self.logger.log(self.state.get_name(), self.current_extension, data_packets.copy())

        self.state.update()

    def set_airbrake_extension(self, extension: float):
        """
        Sets the airbrake extension via the servo. It will be called by the states.
        :param extension: the extension of the airbrakes, between 0 and 1
        """
        self.servo.set_extension(extension)

    def shutdown(self):
        """
        Handles shutting down the airbrakes. This will cause the main loop to break.
        """
        self.set_airbrake_extension(0.0)
        self.imu.stop()
        self.logger.stop()
        self.shutdown_requested = True
