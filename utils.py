"""File which contains a few basic utility functions which can be reused in the project."""

import argparse
from pathlib import Path


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


def convert_to_float(value: str) -> float | None:
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

    parser = argparse.ArgumentParser(
        description="Configuration for the main airbrakes script. "
        "No arguments should be supplied when you are actually launching the rocket."
    )

    parser.add_argument(
        "-m",
        "--mock",
        help="Run in simulation mode with mock data and mock servo",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-r",
        "--real-servo",
        help="Run the mock sim with the real servo",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-l",
        "--keep-log-file",
        help="Keep the log file after the mock sim stops",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-f",
        "--fast-simulation",
        help="Run the mock sim at full speed instead of in real time.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-d",
        "--debug",
        help="Run the mock sim in debug mode. This will not "
        "print the flight data and allow you to inspect the values of your print() statements.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-p",
        "--path",
        help="Define the pathname of flight data to use in mock simulation. Interest Launch data"
        " is used by default",
        type=Path,
        default=False,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        help="Shows the display with much more data.",
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    # Check if the user has passed any options that are only available in simulation mode:
    if (
        any([args.real_servo, args.keep_log_file, args.fast_simulation, args.debug, args.path])
        and not args.mock
    ):
        parser.error(
            "The `--real-servo`, `--keep-log-file`, `--fast-simulation`, `--debug`, and `--path` "
            "options are only available in simulation mode. Please pass `-m` or `--mock` "
            "to run in simulation mode."
        )

    return args
