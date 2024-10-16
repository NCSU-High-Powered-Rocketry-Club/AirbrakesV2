"""File which contains a few basic utility functions which can be reused in the project."""

import multiprocessing
import time
from typing import TYPE_CHECKING

import psutil
from colorama import Fore, Style, init

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
CLEAR_LINE = "\033[K"  # Clear the current line
# Initialize Colorama
init(autoreset=True)  # Automatically reset colors after each print


def update_display(airbrakes: "AirbrakesContext", start_time: float, processes: dict[str, psutil.Process]) -> None:
    """
    Updates the display with real-time data.
    :param airbrakes: The AirbrakesContext object.
    :param start_time: The time (in seconds) the simulation started.
    :param processes: A dictionary of processes to get CPU usage from.
    """
    # Shorten colorama names, I don't love abbreviations but this is a lot of typing and ruff doesn't like when the
    # lines are too long
    g = Fore.GREEN
    r = Fore.RED
    y = Fore.YELLOW
    reset = Style.RESET_ALL

    # Prepare output
    output = [
        f"{y}{'=' * 12} REAL TIME FLIGHT DATA {'=' * 12}{reset}",
        f"Time since sim start:        {g}{time.time() - start_time:<10.2f}{reset} {r}s{reset}",
        f"State:                       {g}{airbrakes.state.name}{reset}",
        f"Current speed:               {g}{airbrakes.data_processor.speed:<10.2f}{reset} {r}m/s{reset}",
        f"Max speed so far:            {g}{airbrakes.data_processor.max_speed:<10.2f}{reset} {r}m/s{reset}",
        f"Current altitude:            {g}{airbrakes.data_processor.current_altitude:<10.2f}{reset} {r}m{reset}",
        f"Max altitude so far:         {g}{airbrakes.data_processor.max_altitude:<10.2f}{reset} {r}m{reset}",
        f"Current airbrakes extension: {g}{airbrakes.current_extension.value}",
        f"{y}{'=' * 13} REAL TIME CPU LOAD {'=' * 14}{reset}",
    ]

    # Add CPU usage data with color coding
    for name, process in processes.items():
        cpu_usage = process.cpu_percent(interval=None)
        if cpu_usage < 50:
            cpu_color = g
        elif cpu_usage < 75:
            cpu_color = y
        else:
            cpu_color = r
        output.append(f"{name:<25}    {cpu_color}CPU Usage: {cpu_usage:>5.2f}% {reset}")

    # Print the output
    print("\n".join(output))

    # Move the cursor up for the next update
    print(MOVE_CURSOR_UP * len(output), end="", flush=True)


def prepare_process_dict(airbrakes: "AirbrakesContext") -> dict[str, psutil.Process]:
    """
    Prepares a dictionary of processes to monitor CPU usage for.
    :param airbrakes: The AirbrakesContext object.
    """
    all_processes = {}
    imu_process = airbrakes.imu._data_fetch_process
    log_process = airbrakes.logger._log_process
    current_process = multiprocessing.current_process()
    for p in [imu_process, log_process, current_process]:
        all_processes[p.name] = psutil.Process(p.pid)
    return all_processes
