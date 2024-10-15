"""File which contains a few basic utility functions which can be reused in the project."""

import multiprocessing
import time
from typing import TYPE_CHECKING
from colorama import Fore, Style, init

import psutil

if TYPE_CHECKING:
    from airbrakes.airbrakes import AirbrakesContext


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


MOVE_CURSOR_UP = "\033[F"  # Move cursor up one line
CLEAR_LINE = "\033[K"       # Clear the current line
# Initialize Colorama
init(autoreset=True)  # Automatically reset colors after each print


def update_display(airbrakes: "AirbrakesContext", start_time: float, processes: dict[str, psutil.Process]) -> None:
    """Prints the values from the simulation in a pretty way."""

    # Prepare output
    output = [
        f"{Fore.YELLOW}{'=' * 12} REAL TIME FLIGHT DATA {'=' * 12}{Style.RESET_ALL}",
        f"Time since sim start:        {Fore.GREEN}{time.time() - start_time:<10.2f}{Style.RESET_ALL} {Fore.RED}s{Style.RESET_ALL}",
        f"State:                       {Fore.GREEN}{airbrakes.state.name}{Style.RESET_ALL}",
        f"Current speed:               {Fore.GREEN}{airbrakes.data_processor.speed:<10.2f}{Style.RESET_ALL} {Fore.RED}m/s{Style.RESET_ALL}",
        f"Max speed so far:            {Fore.GREEN}{airbrakes.data_processor.max_speed:<10.2f}{Style.RESET_ALL} {Fore.RED}m/s{Style.RESET_ALL}",
        f"Current altitude:            {Fore.GREEN}{airbrakes.data_processor.current_altitude:<10.2f}{Style.RESET_ALL} {Fore.RED}m{Style.RESET_ALL}",
        f"Max altitude so far:         {Fore.GREEN}{airbrakes.data_processor.max_altitude:<10.2f}{Style.RESET_ALL} {Fore.RED}m{Style.RESET_ALL}",
        f"Current airbrakes extension: {Fore.GREEN}{airbrakes.current_extension.value}",
        f"{Fore.YELLOW}{'='*13} REAL TIME CPU LOAD {'='*14}{Style.RESET_ALL}",
    ]

    # Add CPU usage data with color coding
    for name, process in processes.items():
        cpu_usage = process.cpu_percent(interval=None)
        if cpu_usage < 50:
            cpu_color = Fore.GREEN
        elif cpu_usage < 75:
            cpu_color = Fore.YELLOW
        else:
            cpu_color = Fore.RED
        output.append(f"{name:<25}    {cpu_color}CPU Usage: {cpu_usage:>5.2f}% {Style.RESET_ALL}")

    # Print the output
    print("\n".join(output))

    # Move the cursor up for the next update
    # Calculate total lines printed and move cursor up accordingly
    print(MOVE_CURSOR_UP * len(output), end="", flush=True)


def prepare_process_dict(airbrakes: "AirbrakesContext") -> dict[str, psutil.Process]:
    all_processes = {}
    imu_process = airbrakes.imu._data_fetch_process
    log_process = airbrakes.logger._log_process
    current_process = multiprocessing.current_process()
    for p in [imu_process, log_process, current_process]:
        all_processes[p.name] = psutil.Process(p.pid)
    return all_processes
