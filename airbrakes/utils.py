"""File which contains a few basic utility functions which can be reused in the project."""

import argparse
import sys
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import multiprocessing


def get_all_from_queue(self, *args, **kwargs) -> list:
    """Used to get all the items from a queue at once. Only relevant if you are running the mock
    replay on Windows, as the multiprocessing.Queue doesn't have a `get_many` method"""
    kwargs.pop("max_messages_to_get", None)  # Argument only used in the Linux version
    return [self.get(*args, **kwargs) for _ in range(self.qsize())]


def get_always_list(self, *args, **kwargs) -> list:
    """Used to get items from the queue, and always returns a list. Only relevant on Windows,
    as the multiprocessing.Queue doesn't have a `get_many` method"""
    fetched = self.get(*args, **kwargs)
    if isinstance(fetched, list):
        return fetched
    return [fetched]


def modify_multiprocessing_queue_windows(obj: "multiprocessing.Queue") -> None:
    """Initializes the multiprocessing queue on Windows by adding the missing methods from the
    faster_fifo library. Modifies `obj` in place.

    :param obj: The multiprocessing.Queue object to add the methods to.
    """
    if sys.platform == "win32":
        obj.get_many = partial(get_always_list, obj)
        obj.put_many = obj.put


def format_date_string(input_string: str) -> str:
    datetime_obj = datetime.fromisoformat(input_string)
    return datetime_obj.strftime("%d{} %B, %Y").format(
        "th"
        if 11 <= datetime_obj.day <= 13
        else {1: "st", 2: "nd", 3: "rd"}.get(datetime_obj.day % 10, "th")
    )


def format_seconds_to_mins_and_secs(seconds: int) -> str:
    """Converts seconds to a string in the format 'm:ss'."""
    return f"{seconds // 60:.0f}:{seconds % 60:02.0f}"


def convert_to_nanoseconds(timestamp_str: str) -> int | None:
    """Converts seconds to nanoseconds, if it isn't already in nanoseconds."""
    try:
        # check if value is already in nanoseconds:
        return int(timestamp_str)
    except ValueError:
        try:
            timestamp_float = float(timestamp_str)
            return int(timestamp_float * 1e9)  # return the value in nanoseconds
        except ValueError:
            return None


def convert_to_seconds(timestamp: float) -> float | None:
    """Converts nanoseconds to seconds"""
    return timestamp / 1e9


def convert_str_to_float(value: str) -> float | None:
    """Converts a value to a float, returning None if the conversion fails."""
    try:
        return float(value)  # Attempt to convert to float
    except (ValueError, TypeError):
        return None  # Return None if the conversion fails


def deadband(input_value: float, threshold: float) -> float:
    """
    Returns 0 if the input_value is within the deadband threshold.
    Otherwise, returns the input_value adjusted by the threshold.
    :param input_value: The value to apply the deadband to.
    :param threshold: The deadband threshold.
    :return: Adjusted input_value or 0 if within the deadband.
    """
    if abs(input_value) < threshold:
        return 0.0
    return input_value


def arg_parser(mock_invocation: bool = False, sim_invocation: bool = False) -> argparse.Namespace:
    """Handles the command line arguments for the main airbrakes script.

    :param mock_invocation: Whether the application is running in mock mode from `uv run mock`.
    Defaults to False, to keep compatibility with the `python -m airbrakes.main` invocation method.
    :param sim_invocation: Whether the application is running in sim mode from `uv run sim`.
    Defaults to False, to keep compatibility with the `python -m airbrakes.main` invocation method.

    :return: The parsed arguments as a class with attributes.
    """

    parser = argparse.ArgumentParser(
        description="Configuration for the main airbrakes script. "
        "No arguments should be supplied when you are actually launching the rocket."
    )

    parser.add_argument(
        "-m",
        "--mock",
        help="Run in replay mode with mock data and mock servo",
        action="store_true",
        default=mock_invocation,
    )

    parser.add_argument(
        "-r",
        "--real-servo",
        help="Run the mock replay with the real servo",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-l",
        "--keep-log-file",
        help="Keep the log file after the mock replay stops",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-f",
        "--fast-replay",
        help="Run the mock replay at full speed instead of in real time.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-d",
        "--debug",
        help="Run the mock replay in debug mode. This will not "
        "print the flight data and allow you to inspect the values of your print() statements.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-c",
        "--real-camera",
        help="Run the mock replay with the real camera.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-p",
        "--path",
        help="Define the pathname of flight data to use in mock replay. Interest Launch data"
        " is used by default",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Shows the display with much more data.",
        action="store_true",
        default=False,
    )

    if sim_invocation:
        parser.add_argument(
            "sim",
            help="Runs the data simulation alongside the mock simulation, with an optional scale",
            choices=["full-scale", "sub-scale", "legacy"],
            nargs="?",  # Allows an optional argument
            default="full-scale",  # Default when `-s` is provided without a value
        )

    args = parser.parse_args()

    if not hasattr(args, "sim"):
        args.sim = False

    # Check if the user has passed any options that are only available in mock replay mode:
    if (
        any(
            [
                args.real_servo,
                args.keep_log_file,
                args.fast_replay,
                args.path,
                args.real_camera,
                args.sim,
            ]
        )
        and not args.mock
    ):
        parser.error(
            "The `--real-servo`, `--keep-log-file`, `--fast-replay`, `sim`, and `--path` "
            "options are only available in mock replay mode. Please pass `-m` or `--mock` "
            "to run in mock replay mode."
        )

    if args.verbose and args.debug:
        parser.error("The `--verbose` and `--debug` options cannot be used together.")

    if args.sim and args.path:
        parser.error("The `--path` option is not able to be used with the `sim` option")
    return args
