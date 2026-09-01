"""
Module which contains the MockServo class and doesn't use the adafruit
circuitpython library.
"""

import threading

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import SERVO_DELAY_SECONDS, SERVO_MIN_EXTENSION, SERVO_MAX_EXTENSION
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


class MockServo(BaseServo):
    """
    A custom class that represents a mock servo motor.
    """

    __slots__ = (
        "_go_to_max_no_buzz",
        "_go_to_min_no_buzz",
        "_servo_extension",
    )

    def __init__(self) -> None:
        """Initialize the mock servo in its minimum-safe position."""
        self._servo_extension = SERVO_MIN_EXTENSION
        self._go_to_max_no_buzz: threading.Timer | None = None
        self._go_to_min_no_buzz: threading.Timer | None = None

    def start(self) -> None:
        """Start the mock servo; no real hardware is required."""
        self._servo_extension = SERVO_MIN_EXTENSION

    def stop(self) -> None:
        """Stop the mock servo and cancel any pending motion timers."""
        self._cancel_timer("_go_to_max_no_buzz")
        self._cancel_timer("_go_to_min_no_buzz")

    def extend_airbrakes(self) -> None:
        """Command the mock servo to the maximum extension."""
        self._cancel_timer("_go_to_min_no_buzz")
        self._set_extension(SERVO_MAX_EXTENSION)
        self._go_to_max_no_buzz = threading.Timer(
            SERVO_DELAY_SECONDS,
            self._set_extension,
            args=(SERVO_MAX_EXTENSION,),
        )
        self._go_to_max_no_buzz.start()

    def retract_airbrakes(self) -> None:
        """Command the mock servo back to the minimum extension."""
        self._cancel_timer("_go_to_max_no_buzz")
        self._set_extension(SERVO_MIN_EXTENSION)
        self._go_to_min_no_buzz = threading.Timer(
            SERVO_DELAY_SECONDS,
            self._set_extension,
            args=(SERVO_MIN_EXTENSION,),
        )
        self._go_to_min_no_buzz.start()

    def _set_extension(self, extension: float) -> None:
        """Update the current commanded servo extension."""
        self._servo_extension = extension

    def _cancel_timer(self, timer_name: str) -> None:
        """Cancel a pending timer, if present."""
        timer = getattr(self, timer_name)
        if timer is not None:
            timer.cancel()

    @property
    def servo_extension(self) -> float:
        """Return the most recently commanded extension."""
        return self._servo_extension

    @property
    def battery_volts(self) -> float:
        """Return mock battery voltage in volts."""
        return 0.0

    @property
    def system_current_milliamps(self) -> float:
        """Return mock system current in milliamps."""
        return 0.0

    @property
    def servo_voltage(self) -> float:
        """Return mock servo voltage in volts."""
        return 0.0

    @property
    def servo_temp(self) -> float:
        """Return mock servo temperature in degrees Celsius."""
        return 0.0

    def get_servo_data_packet(self) -> ServoDataPacket:
        """
        Creates the servo data packet from the mock servo data.

        :return: The servo data packet.
        """
        return ServoDataPacket(
            current_position=self.servo_extension,
            system_current_milliamps=self.system_current_milliamps,
            battery_volts=self.battery_volts,
            voltage=self.servo_voltage,
            current_temp=self.servo_temp,
        )
