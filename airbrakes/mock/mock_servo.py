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

    __slots__ = ("_is_powered", "_servo_extension", "extend", "retract")

    def __init__(self) -> None:
        """Initialize an unpowered mock servo at minimum extension."""
        self._servo_extension = SERVO_MIN_EXTENSION
        self.extend: threading.Timer | None = None
        self.retract: threading.Timer | None = None
        self._is_powered = False

    def start(self) -> None:
        """Power on the mock servo and reset it to minimum extension."""
        self._servo_extension = SERVO_MIN_EXTENSION
        self._is_powered = True

    def stop(self) -> None:
        """Power off the mock servo and cancel pending motion timers."""
        self._cancel_timer("extend")
        self._cancel_timer("retract")
        self._is_powered = False

    def extend_airbrakes(self) -> None:
        """Request maximum extension and schedule its delayed completion."""
        self._cancel_timer("retract")
        self.set_extension(SERVO_MAX_EXTENSION)
        self.extend = threading.Timer(
            SERVO_DELAY_SECONDS,
            self.set_extension,
            args=(SERVO_MAX_EXTENSION,),
        )
        self.extend.start()

    def retract_airbrakes(self) -> None:
        """Request minimum extension and schedule its delayed completion."""
        self._cancel_timer("extend")
        self.set_extension(SERVO_MIN_EXTENSION)
        self.retract = threading.Timer(
            SERVO_DELAY_SECONDS,
            self.set_extension,
            args=(SERVO_MIN_EXTENSION,),
        )
        self.retract.start()

    def set_extension(self, angle: float) -> None:
        """Record a commanded servo position in degrees."""
        self._servo_extension = angle

    def _cancel_timer(self, timer_name: str) -> None:
        """Cancel the pending timer stored under ``timer_name``, if any."""
        timer = getattr(self, timer_name)
        if timer is not None:
            timer.cancel()

    @property
    def is_powered(self) -> bool:
        """Return whether the mock servo is powered."""
        return self._is_powered

    @property
    def servo_extension(self) -> float:
        """Return the most recently recorded servo position."""
        return self._servo_extension

    @property
    def battery_volts(self) -> float:
        """Return the mock battery voltage."""
        return 0.0

    @property
    def system_current_milliamps(self) -> float:
        """Return the mock system current."""
        return 0.0

    @property
    def servo_voltage(self) -> float:
        """Return the mock servo voltage."""
        return 0.0

    @property
    def servo_temp(self) -> float:
        """Return mock servo temperature in degrees Celsius."""
        return 0.0

    def get_servo_data_packet(self) -> ServoDataPacket:
        """Create a data packet from the mock servo's telemetry."""
        return ServoDataPacket(
            current_position=self.servo_extension,
            system_current_milliamps=self.system_current_milliamps,
            battery_volts=self.battery_volts,
            voltage=self.servo_voltage,
            current_temp=self.servo_temp,
        )
