from Airbrakes.imu import IMU, IMUDataPacket
from Airbrakes.logger import Logger
from Airbrakes.servo import Servo
from state import *


class AirbrakesContext:
    """
    Manages the state machine for the rocket's airbrakes system, keeping track of the current state and communicating
    with hardware like the servo and IMU. This class is what connects the state machine to the hardware.

    Read more about the state machine pattern here: https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

    __slots__ = (
        "logger",
        "servo",
        "imu",
        "state",
        "shutdown_requested",
        "current_extension",
        "current_imu_data",
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
        Called every loop iteration. Depending on the current state, it will do different things. It
        is what controls the airbrakes and chooses when to move to the next state.
        """
        # Gets the current extension and IMU data, the states will use these values
        self.current_extension = self.servo.extension
        self.current_imu_data = self.imu.get_imu_data()

        # Logs the current state, extension, and IMU data
        self.logger.log(self.state.get_name(), self.current_extension, self.current_imu_data)

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
