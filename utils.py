"""File which contains a few basic utility functions which can be reused in the project."""

import multiprocessing
import time
from typing import TYPE_CHECKING, Literal

import psutil
from colorama import Fore, Style, init

if TYPE_CHECKING:
    from airbrakes.airbrakes import AirbrakesContext


G = Fore.GREEN
R = Fore.RED
Y = Fore.YELLOW
RESET = Style.RESET_ALL


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


class FlightDisplay:
    """Class related to displaying real-time flight data in the terminal with pretty colors
    and spacing.
    """

    # Initialize Colorama
    init(autoreset=True)  # Automatically reset colors after each print
    MOVE_CURSOR_UP = "\033[F"  # Move cursor up one line
    NATURAL_END = "natural"
    INTERRUPTED_END = "interrupted"

    __slots__ = ("airbrakes", "processes", "start_time")

    def __init__(self, airbrakes: "AirbrakesContext", start_time: float) -> None:
        """
        :param airbrakes: The AirbrakesContext object.
        :param start_time: The time (in seconds) the simulation started.
        """
        self.airbrakes = airbrakes
        self.start_time = start_time
        # Prepare the processes for monitoring in the simulation:
        self.processes = self.prepare_process_dict()

    def update_display(self, end_sim: Literal["natural", "interrupted"] | bool = False) -> None:
        """
        Updates the display with real-time data.
        :param end_sim: Whether the simulation ended or was interrupted.
        """
        # Shorten colorama names, I don't love abbreviations but this is a lot of typing and ruff doesn't like when the
        # lines are too long

        try:
            current_queue_size = self.airbrakes.imu._data_queue.qsize()
        except NotImplementedError:  # Returns NotImplementedError on arm architecture (Raspberry Pi)
            current_queue_size = "N/A"

        # Prepare output
        output = [
            f"{Y}{'=' * 12} REAL TIME FLIGHT DATA {'=' * 12}{RESET}",
            f"Time since sim start:        {G}{time.time() - self.start_time:<10.2f}{RESET} {R}s{RESET}",
            f"State:                       {G}{self.airbrakes.state.name:<15}{RESET}",
            f"Current speed:               {G}{self.airbrakes.data_processor.speed:<10.2f}{RESET} {R}m/s{RESET}",
            f"Max speed so far:            {G}{self.airbrakes.data_processor.max_speed:<10.2f}{RESET} {R}m/s{RESET}",
            f"Current height:            {G}{self.airbrakes.data_processor.current_altitude:<10.2f}{RESET} {R}m{RESET}",
            f"Max height so far:         {G}{self.airbrakes.data_processor.max_altitude:<10.2f}{RESET} {R}m{RESET}",
            f"Current airbrakes extension: {G}{self.airbrakes.current_extension.value}{RESET}",
            f"IMU Data Queue Size:         {G}{current_queue_size}{RESET}",
            f"{Y}{'=' * 13} REAL TIME CPU LOAD {'=' * 14}{RESET}",
        ]

        # Add CPU usage data with color coding
        for name, process in self.processes.items():
            cpu_usage = process.cpu_percent(interval=None)
            if cpu_usage < 50:
                cpu_color = G
            elif cpu_usage < 75:
                cpu_color = Y
            else:
                cpu_color = R
            output.append(f"{name:<25}    {cpu_color}CPU Usage: {cpu_usage:>6.2f}% {RESET}")

        # Print the output
        print("\n".join(output))

        # Move the cursor up for the next update, if the simulation hasn't ended:
        if not end_sim:
            print(self.MOVE_CURSOR_UP * len(output), end="", flush=True)

        # Print the end of simulation message if the simulation has ended
        if end_sim == self.NATURAL_END:
            # Print the end of simulation header
            print(f"{Fore.RED}{'=' * 14} END OF SIMULATION {'=' * 14}{Style.RESET_ALL}")
        elif end_sim == self.INTERRUPTED_END:
            print(f"{Fore.RED}{'=' * 12} INTERRUPTED SIMULATION {'=' * 13}{Style.RESET_ALL}")

    def prepare_process_dict(self) -> dict[str, psutil.Process]:
        """
        Prepares a dictionary of processes to monitor CPU usage for.
        """
        all_processes = {}
        imu_process = self.airbrakes.imu._data_fetch_process
        log_process = self.airbrakes.logger._log_process
        current_process = multiprocessing.current_process()
        for p in [imu_process, log_process, current_process]:
            all_processes[p.name] = psutil.Process(p.pid)
        return all_processes
