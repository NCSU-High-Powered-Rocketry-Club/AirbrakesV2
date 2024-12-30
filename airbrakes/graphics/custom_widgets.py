"""Module which contains custom widgets for the display."""

import textual.renderables.digits
from textual.renderables.digits import DIGITS
from textual.widgets import Digits

UNICODE_T = """─┬─
 │
 ╵
"""

# Define constants for time conversions
NANOS_PER_SECOND = 1_000_000_000  # 1 second
NANOS_PER_MINUTE = 60 * NANOS_PER_SECOND  # 60 seconds
NANOS_PER_CENTISECOND = NANOS_PER_SECOND // 100  # 1 centisecond = 10,000,000 ns


def add_unicode_T_to_digits():
    """Hack to modify the textual library code to include a 3x3 version of the letter 'T', so we
    can include it in the flight time display."""
    textual.renderables.digits.DIGITS = f"{DIGITS}T"
    textual.renderables.digits.DIGITS3X3.extend(UNICODE_T.splitlines())
    textual.renderables.digits.DIGITS3X3_BOLD.extend(UNICODE_T.splitlines())


class TimeDisplay(Digits):
    """A widget to display elapsed flight time"""

    add_unicode_T_to_digits()

    @staticmethod
    def format_ns_to_min_s_ms(ns: int) -> str:
        """
        Formats a time in nanoseconds to a string in the format MM:SS:ms.

        :param ns: The time in nanoseconds.
        :return: The formatted time string.
        """

        # Calculate minutes and the remaining nanoseconds
        minutes, remainder_ns = divmod(ns, NANOS_PER_MINUTE)

        # Calculate seconds and the remaining nanoseconds
        seconds, remainder_ns = divmod(remainder_ns, NANOS_PER_SECOND)

        # Calculate centiseconds
        centiseconds = (remainder_ns // NANOS_PER_CENTISECOND) % 100

        return f"{minutes:02}:{seconds:02}.{centiseconds:02}"
