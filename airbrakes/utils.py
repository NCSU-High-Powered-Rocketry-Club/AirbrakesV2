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


def convert_to_nanoseconds(timestamp_str: str) -> int:
    """
    Converts seconds to nanoseconds, if it isn't already in nanoseconds.
    """
    try:
        # check if value is already in nanoseconds:
        return int(timestamp_str)
    except ValueError:
        timestamp_float = float(timestamp_str)
        return int(timestamp_float * 1e9)  # return the value in nanoseconds


def convert_ns_to_s(nanoseconds: int) -> float:
    """
    Converts nanoseconds to seconds.

    :param nanoseconds: The time in nanoseconds.
    :return: The time in seconds.
    """
    return nanoseconds * 1e-9


def convert_seconds_to_packets(
    seconds: float, raw_packet_freq: float, est_packet_freq: float
) -> int:
    """
    Returns the number of packets which are expected to be received, given the time in seconds, the
    raw packet rate, and the estimated packet rate.

    :param seconds: The time in seconds.
    :param raw_packet_freq: The raw packet rate, in Hz.
    :param est_packet_freq: The estimated packet rate, in Hz.
    :return: The number of packets expected to be received.
    """
    # Formula for converting number of packets to seconds and vice versa:
    # If N = total number of packets, T = total time in seconds:
    # f = EstimatedDataPacket.frequency + RawDataPacket.frequency = 500 + 500 = 1000 Hz
    # T = N/f => N = T * 1000

    # Calculate the number of packets expected to be received:
    return int(seconds * (raw_packet_freq + est_packet_freq))


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

    :return: The parsed arguments as a class with attributes.
    """
    # We require ONE and only one of the 3 positional arguments to be passed:
    # - real: Run the real flight with all the real hardware.
    # - mock: Run in mock replay mode with mock data.
    global_parser = argparse.ArgumentParser(add_help=False)

    # Top-level parser for the main script:
    main_parser = argparse.ArgumentParser(
        description="Main parser for the Airbrakes program.",
        parents=[global_parser],
    )

    # Subparsers for `real` or `mock`
    subparsers = main_parser.add_subparsers(
        title="modes", description="Valid modes of operation", dest="mode", required=True
    )

    # Real flight parser:
    real_parser = subparsers.add_parser(
        "real",
        help="Run the real flight with all the real hardware by default.",
        description="Configuration for the real flight. Uses real hardware unless specified.",
        parents=[global_parser],
        prog="real",
    )
    real_parser.add_argument(
        "-s",
        "--mock-servo",
        help="Run the real flight with a mock servo instead of the real servo.",
        action="store_true",
        default=False,
    )

    # Mock replay parser:
    mock_replay_parser = subparsers.add_parser(
        "mock",
        help="Run in replay mode with mock data (i.e. previous flight data)",
        description="Configuration for the mock replay Airbrakes program.",
        parents=[global_parser],  # Include the global options
        prog="mock",  # Program name in help messages
    )
    add_common_arguments(mock_replay_parser)

    parsed_args = main_parser.parse_args()
    # If benchmark mode is enabled, set fast replay to True
    if parsed_args.mode != "real" and parsed_args.bench:
        parsed_args.fast_replay = True

    return parsed_args


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Adds the arguments common to the mock replay.

    :param parser: the mock replay subparser.
    """
    # TODO: add sim back with HPRM
    _type = "mock replay"

    parser.add_argument(
        "-s",
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
        "-b",
        "--bench",
        help=f"Run the {_type} in benchmark mode. This disables the display and simply shows the "
        "flight data after it has finished. Implies --fast-replay.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-t",
        "--target-apogee",
        help=f"Set the target apogee for the {_type}. Defaults to the value in the metadata for "
        "mock replays.",
        type=float,
        default=None,
    )

    parser.add_argument(
        "-p",
        "--path",
        help="Define the pathname of flight data to use in the mock replay. The first file"
        " found in the launch_data directory will be used if not specified.",
        type=Path,
        default=None,
    )
