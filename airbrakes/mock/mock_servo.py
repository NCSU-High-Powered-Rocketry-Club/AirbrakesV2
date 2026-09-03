"""Mock implementation of the current Lewan servo interface."""

import threading

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import (
    SERVO_DELAY_SECONDS,
    SERVO_MAX_EXTENSION,
    SERVO_MIN_EXTENSION,
)
from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


class MockServo(BaseServo):
    """
    A custom class that represents a mock servo motor.
    """

    __slots__ = ("_servo_extension", "extend", "retract", "_is_powered")

    def __init__(self) -> None:
        """Initialize the mock servo in its minimum-safe position."""
        self._servo_extension = SERVO_MIN_EXTENSION
        self.extend: threading.Timer | None = None
        self.retract: threading.Timer | None = None
        self._is_powered = False

    def start(self) -> None:
        """Start the mock servo; no real hardware is required."""
        self._servo_extension = SERVO_MIN_EXTENSION
        self._is_powered = True

    def stop(self) -> None:
        """Stop the mock servo and cancel any pending motion timers."""
        self._cancel_timer("extend")
        self._cancel_timer("retract")
        self._is_powered = False

    def extend_airbrakes(self) -> None:
        """Command the mock servo to the maximum extension."""
        self._cancel_timer("retract")
        self.set_extension(SERVO_MAX_EXTENSION)
        self.extend = threading.Timer(
            SERVO_DELAY_SECONDS,
            self.set_extension,
            args=(SERVO_MAX_EXTENSION,),
        )
        self.extend.start()

    def retract_airbrakes(self) -> None:
        """Command the mock servo back to the minimum extension."""
        self._cancel_timer("extend")
        self.set_extension(SERVO_MIN_EXTENSION)
        self.retract = threading.Timer(
            SERVO_DELAY_SECONDS,
            self.set_extension,
            args=(SERVO_MIN_EXTENSION,),
        )
        self.retract.start()

    def set_extension(self, angle: float) -> None:
        """Record the position sent to the mocked servo."""
        self._servo_extension = angle

    def _cancel_timer(self, timer_name: str) -> None:
        """Cancel a pending timer, if present."""
        timer = getattr(self, timer_name)
        if timer is not None:
            timer.cancel()

    @property
    def is_powered(self) -> bool:
        """Return the power state of the mock servo."""
        return self._is_powered
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
