"""
Module which contains the MockServo class and doesn't use the adafruit
circuitpython library.
"""

from airbrakes.base_classes.base_servo import BaseServo


class MockServo(BaseServo):
    """
    A custom class that represents a mock servo motor.
    """

    __slots__ = ()

    def __init__(self) -> None:
        """
        Initializes the mock servo object.
        """
        pass

    def start(self) -> None:
        """
        Starts the servo.
        """
        pass

    def stop(self) -> None:
        """
        Stops the servo.
        """
        pass

    def extend_airbrakes(self) -> None:
        """
        Extends the servo to deploy the airbrakes (Mock).
        """
        pass

    def retract_airbrakes(self) -> None:
        """
        Retracts the servo to close the airbrakes (Mock).
        """
        pass

    def get_battery_volts(self) -> float:
        """
        Gets the current system voltage in volts. Since this is a mock servo,
        it always returns 0.

        :return: The current system voltage in volts.
        """
        return 0.0

    def get_system_current_milliamps(self) -> float:
        """
        Gets the current system current in milliamps. Since this is a mock
        servo, it always returns 0.

        :return: The current system current in milliamps.
        """
        return 0.0