"""
"""

from airbrakes.constants import ServoExtension
from airbrakes.base_classes.base_servo import BaseServo


class MockServo(BaseServo):
    """Very small mock: holds an angle and exposes simple control methods."""

    __slots__ = (
        "_current_extension",
        "servo_id",
    )

    def __init__(self, servo_id: int, port: str) -> None:
        """

        Create a mock servo.

        :param servo_id: arbitrary identifier
        """
        super().__init__()
        self.servo_id = servo_id
        self._current_extension = ServoExtension.MIN_EXTENSION

    @property
    def current_extension(self) -> ServoExtension:
        return self._current_extension

    def set_max_extension(self) -> None:
        """
        Set servo to maximum extension.
        """
        self._current_extension = ServoExtension.MAX_EXTENSION

    def set_min_extension(self) -> None:
        """
        Set servo to minimum extension.
        """
        self._current_extension = ServoExtension.MIN_EXTENSION
