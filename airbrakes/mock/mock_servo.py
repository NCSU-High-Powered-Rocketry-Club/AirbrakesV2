"""
"""

from airbrakes.constants import ServoExtension
from airbrakes.base_classes.base_servo import BaseServo


class MockServo(BaseServo):
    """Very small mock: holds an angle and exposes simple control methods."""

    __slots__ = (
        "current_extension",
        "servo",
        "servo_id",
    )

    def __init__(self, servo_id: int, _port: str | None = None) -> None:
        """

        Create a mock servo.

        :param servo_id: arbitrary identifier (kept for compatibility with fixtures)
        :param _port: unused, kept for API compatibility
        """
        super().__init__()
        self.servo_id = servo_id
        # Provide a simple mock servo bus object for compatibility with tests
        # Many tests expect `servo.servo` to be an instance of MockServo (module's MockServo),
        # so point `servo` to this instance for compatibility.
        self.servo = MockBus(_port)
        self.current_extension: ServoExtension

    def set_max_extension(self) -> None:
        """
        Set servo to maximum extension.
        """
        self.current_extension = self.servo.set_min_extension()

    def set_min_extension(self) -> None:
        """
        Set servo to minimum extension.
        """
        self.current_extension = self.servo.set_min_extension()

class MockBus:
    """A tiny mock of the servo bus used by the real hardware class."""

    __slots__ = ("port",)

    def __init__(self, port: str | None = None) -> None:
        self.port = port

    def set_max_extension(self) -> ServoExtension:
        return ServoExtension.MAX_EXTENSION

    def set_min_extension(self) -> ServoExtension:
        return ServoExtension.MIN_EXTENSION
