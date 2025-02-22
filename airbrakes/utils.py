"""File which contains utility functions which can be reused in the project, along with handling
command line arguments"""

import argparse
import sys
import warnings
from pathlib import Path
from typing import Any

import psutil


def _convert_unknown_type_to_float(obj_type: Any) -> float:
    """
    Converts the object to a float. Used by msgspec to convert numpy float64 to a float.
    :param obj_type: The object to convert.
    :return: The converted object.
    """
    return float(obj_type)


def set_process_priority(nice_value: int) -> None:
    """Sets the priority of the calling process to the specified nice value. Only works on Linux."""
    if sys.platform != "win32":
        p = psutil.Process()
        try:
            p.nice(nice_value)
        except psutil.AccessDenied:
            warnings.warn(
                f"Could not set process priority to {nice_value}. Please run the program as root "
                "to set process priority.",
                stacklevel=2,
            )


def deadband(input_value: float, threshold: float) -> float:
    """
    Returns 0.0 if input_value is within the deadband threshold. Otherwise, returns input_value
        adjusted by the threshold.
    :param input_value: The value to apply the deadband to.
    :param threshold: The deadband threshold.
    :return: Adjusted input_value or 0.0 if within the deadband.
    """
    if abs(input_value) < threshold:
        return 0.0
    return input_value


def arg_parser() -> argparse.Namespace:
    """
    Handles the command line arguments for the main Airbrakes program.
    :return: The parsed arguments as a class with attributes.
    """
    # We require ONE and only one of the 3 positional arguments to be passed:
    # - real: Run the real flight with all the real hardware.
    # - mock: Run in mock replay mode with mock data.
    # - sim: Runs the flight simulation alongside the mock replay, with an optional preset
    #   selection.
    global_parser = argparse.ArgumentParser(add_help=False)

    # Global mutually exclusive group, for the `--debug` and `--verbose` options:
    global_group = global_parser.add_mutually_exclusive_group()

    # These are global options, available to `mock`, `real`, and `sim` modes:
    global_group.add_argument(
        "-d",
        "--debug",
        help="Run the flight without a display. This will not print the flight data and allow "
        "you to inspect the values of your print() statements.",
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
        description="Main parser for the Airbrakes program.",
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

    # Mock replay parser:
    mock_replay_parser = subparsers.add_parser(
        "mock",
        help="Run in replay mode with mock data (i.e. previous flight data)",
        description="Configuration for the mock replay Airbrakes program.",
        parents=[global_parser],  # Include the global options
        prog="mock",  # Program name in help messages
    )
    add_common_arguments(mock_replay_parser, is_mock=True)

    # Sim parser
    sim_parser = subparsers.add_parser(
        "sim",
        help="Runs the flight simulation alongside the mock replay.",
        description="Configuration for the flight simulation alongside the mock replay.",
        parents=[global_parser],  # Include the global options
        prog="sim",  # Program name in help messages
    )

    sim_parser.add_argument(
        "preset",
        help="Selects the preset to use for the simulation.",
        choices=["full-scale", "sub-scale", "legacy", "pelicanator"],
        nargs="?",  # Optional
        default="full-scale",
    )
    add_common_arguments(sim_parser, is_mock=False)

    return main_parser.parse_args()


def add_common_arguments(parser: argparse.ArgumentParser, is_mock: bool = True) -> None:
    """
    Adds the arguments common to the mock replay and the sim to the parser.
    :param parser: the mock replay or sim subparser.
    :param is_mock: Whether running in mock replay mode.
    """

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
            help="Define the pathname of flight data to use in the mock replay. The first file"
            " found in the launch_data directory will be used if not specified.",
            type=Path,
            default=None,
        )
