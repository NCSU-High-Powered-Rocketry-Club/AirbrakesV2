from Airbrakes.imu import IMU
from Airbrakes.servo import Servo
from state import *


class AirbrakesContext:
    """
    Manages the state machine for the rocket's airbrakes system, keeping track of the current state and communicating
    with hardware like the servo and IMU. This class is what connects the state machine to the hardware.

    Read more about the state machine pattern here: https://www.tutorialspoint.com/design_pattern/state_pattern.htm
    """

    def __init__(self, servo: Servo, imu: IMU):
        self.servo = servo
        self.imu = imu
        self.state: State = StandByState(self)
        self.shutdown_requested = False

    def update(self):
        """
        Called every loop iteration. Depending on the current state, it will do different things. It
        is what controls the airbrakes and chooses when to move to the next state.
        """
        self.state.update()

    def shutdown(self):
        """
        Handles shutting down the airbrakes. This will cause the main loop to break.
        """
        self.shutdown_requested = True

    def set_airbrake_extension(self, extension: float):
        """
        Sets the airbrake extension via the servo. It will be called by the states.
        """
        self.servo.set_extension(extension)

    def get_imu_reading(self):
        """
        Gets the current reading from the IMU. It will be called by the states.
        """
        return self.imu.get_reading()
