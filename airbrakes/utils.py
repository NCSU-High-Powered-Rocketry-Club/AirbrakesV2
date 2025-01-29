"""File which contains a few basic utility functions which can be reused in the project."""

import argparse
import sys
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


def arg_parser() -> argparse.Namespace:
    """Handles the command line arguments for the main airbrakes script.

    :return: The parsed arguments as a class with attributes.
    """
    # We require ONE and only one of the 3 positional arguments to be passed:
    # - real: Run the real flight with all the real hardware.
    # - mock: Run in replay mode with mock data and mock servo.
    # - sim: Runs the data simulation alongside the mock simulation, with an optional scale.
    global_parser = argparse.ArgumentParser(add_help=False)

    # Global mutually exclusive group, for the `--debug` and `--verbose` options:
    global_group = global_parser.add_mutually_exclusive_group()

    # These are global options, available to `mock`, `real`, and `sim` modes:
    global_group.add_argument(
        "-d",
        "--debug",
        help="Run the flight without a display. This will not "
        "print the flight data and allow you to inspect the values of your print() statements.",
        action="store_true",
        default=False,
    )

    global_group.add_argument(
        "-v",
        "--verbose",
        help="Shows the display with much more data.",
        action="store_true",
        default=False,
    )

    # Top-level parser for the main script:
    main_parser = argparse.ArgumentParser(
        description="Main parser for the airbrakes script.",
        parents=[global_parser],
    )

    # Subparsers for `real`, `mock`, and `sim`
    subparsers = main_parser.add_subparsers(
        title="modes", description="Valid modes of operation", dest="mode", required=True
    )

    # Real flight parser:
    subparsers.add_parser(
        "real",
        help="Run the real flight with all the real hardware.",
        description="Configuration for the real flight.",
        parents=[global_parser],  # Include the global options
        prog="real",  # Program name in help messages
    )
    # No extra arguments needed for the real flight mode.

    # Mock replay parser:
    mock_replay_parser = subparsers.add_parser(
        "mock",
        help="Run in replay mode with mock data (i.e. previous flight data)",
        description="Configuration for the mock replay airbrakes script.",
        parents=[global_parser],  # Include the global options
        prog="mock",  # Program name in help messages
    )
    add_common_arguments(mock_replay_parser, is_mock=True)

    # Sim parser
    sim_parser = subparsers.add_parser(
        "sim",
        help="Runs the data simulation alongside the mock simulation.",
        description="Configuration for the data simulation alongside the mock simulation.",
        parents=[global_parser],  # Include the global options
        prog="sim",  # Program name in help messages
    )

    sim_parser.add_argument(
        "scale",
        help="Simulation scale.",
        choices=["full-scale", "sub-scale", "legacy"],
        nargs="?",  # Optional
        default="full-scale",
    )

    add_common_arguments(sim_parser, is_mock=False)

    return main_parser.parse_args()


def add_common_arguments(parser: argparse.ArgumentParser, is_mock: bool = True) -> None:
    """Adds the arguments common to the mock replay and the sim to the parser."""

    _type = "mock replay" if is_mock else "sim"

    parser.add_argument(
        "-r",
        "--real-servo",
        help=f"Run the {_type} with the real servo",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-l",
        "--keep-log-file",
        help=f"Keep the log file after the {_type} stops",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-f",
        "--fast-replay",
        help=f"Run the {_type} at full speed instead of in real time.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-c",
        "--real-camera",
        help=f"Run the {_type} with the real camera.",
        action="store_true",
        default=False,
    )

    if is_mock:
        parser.add_argument(
            "-p",
            "--path",
            help="Define the pathname of flight data to use in mock replay. By default, the"
            " first file found in the launch_data directory will be used if not specified.",
            type=Path,
            default=None,
        )
