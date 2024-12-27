"""Module which contains custom widgets for the display."""

import textual.renderables.digits
from textual.renderables.digits import DIGITS
from textual.widgets import Digits

unicode_T = """─┬─
 │
 ╵
"""


def add_unicode_T_to_digits():
    """Hack to modify the textual library code to include a 3x3 version of the letter 'T', so we
    can include it in the flight time display."""
    textual.renderables.digits.DIGITS = f"{DIGITS}T"
    textual.renderables.digits.DIGITS3X3.extend(unicode_T.splitlines())
    textual.renderables.digits.DIGITS3X3_BOLD.extend(unicode_T.splitlines())


class TimeDisplay(Digits):
    """A widget to display elapsed flight time"""

    add_unicode_T_to_digits()

    @staticmethod
    def format_ns_to_min_s_ms(ns: int) -> str:
        """
        Formats a time in nanoseconds to a string in the format MM:SS:ms.
        :param: ns: The time in nanoseconds.

        :return: The formatted time string.
        """

        # Convert nanoseconds to seconds
        s = ns / 1e9

        # Get the minutes
        m = s // 60
        s %= 60

        # Get the milliseconds
        ms = (s % 1) * 100

        return f"{m:02.0f}:{s:02.0f}.{ms:02.0f}"
