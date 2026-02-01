"""
File which contains utility functions which can be reused in the project, along with handling
command line arguments.
"""

import argparse
import queue
from pathlib import Path
from typing import Any


def convert_unknown_type_to_float(obj_type: Any) -> float:
    """
    Converts the object to a float.

    Used by msgspec to convert numpy float64 to a float.
    :param obj_type: The object to convert.
    :return: The converted object.
    """
    return float(obj_type)


def convert_ns_to_s(nanoseconds: int) -> float:
    """
    Converts nanoseconds to seconds.

    :param nanoseconds: The time in nanoseconds.
    :return: The time in seconds.
    """
    return nanoseconds * 1e-9


def convert_s_to_ns(seconds: float) -> float:
    """
    Converts seconds to nanoseconds.

    :param seconds: The time in seconds.
    :return: The time in nanoseconds.
    """
    return seconds * 1e9


def get_all_packets_from_queue(packet_queue: queue.SimpleQueue, block: bool) -> list[Any]:
    """
    Empties the queue and returns all the items in a list.

    :param packet_queue: The queue to empty.
    :param block: Whether to block when getting items from the queue.

    :return: A list of all the items in the queue.
    """
    items = []

    if block:
        # Block until at least one item is available
        items.append(packet_queue.get(block=True))

    # Drain the rest of the queue, non-blocking
    while not packet_queue.empty():
        try:
            items.append(packet_queue.get(block=False))
        except queue.Empty:
            break
    return items


def deadband(input_value: float, threshold: float) -> float:
    """
    Returns 0.0 if input_value is within the deadband threshold.

    Otherwise, returns input_value adjusted by the threshold.
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
    """

    # We define this as a parent so we can use it in both sub-commands
    common_parser = argparse.ArgumentParser(add_help=False)
    common_group = common_parser.add_mutually_exclusive_group()
    common_group.add_argument(
        "-d", "--debug",
        action="store_true",
        help="Run without a display to inspect print() statements."
    )
    common_group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show the display with extended data."
    )

    # Main Parser
    parser = argparse.ArgumentParser(
        description="Main parser for the Airbrakes program.",
        parents=[common_parser]
    )

    subparsers = parser.add_subparsers(
        title="modes",
        dest="mode",
        required=True
    )

    # Real Flight Parser
    real_parser = subparsers.add_parser(
        "real",
        parents=[common_parser],
        help="Run real flight with hardware.",
        description="Configuration for the real flight."
    )
    real_parser.add_argument(
        "-s", "--mock-servo",
        action="store_true",
        help="Run the real flight with a mock servo."
    )
    real_parser.add_argument(
        "-p",
        "--pretend-firm",
        help="Make FIRM output data from a previous FIRM log file.",
        type=Path,
        metavar="LOG_FILE"
    )

    # Mock Replay Parser
    mock_parser = subparsers.add_parser(
        "mock",
        parents=[common_parser],
        help="Run in replay mode with mock data.",
        description="Configuration for the mock replay."
    )

    # Inlined arguments (previously in add_common_arguments)
    mock_parser.add_argument(
        "-s", "--real-servo",
        action="store_true",
        help="Run the mock replay with the real servo."
    )
    mock_parser.add_argument(
        "-l", "--keep-log-file",
        action="store_true",
        help="Keep the log file after replay stops."
    )
    mock_parser.add_argument(
        "-f", "--fast-replay",
        action="store_true",
        help="Run replay at full speed."
    )
    mock_parser.add_argument(
        "-p", "--path",
        type=Path,
        help="Path to flight data file (defaults to first in launch_data)."
    )

    return parser.parse_args()
