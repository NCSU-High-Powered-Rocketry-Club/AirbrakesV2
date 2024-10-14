"""File which contains a few basic utility functions which can be reused in the project."""

import multiprocessing
import time
from typing import TYPE_CHECKING

import psutil

if TYPE_CHECKING:
    from airbrakes.airbrakes import AirbrakesContext

# ANSI escape code for cursor movement for printing simulation data:
MOVE_CURSOR_UP = "\033[F"  # Move the cursor one line up


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


def convert_to_float(value: str | int) -> float | None:
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


def update_display(airbrakes: "AirbrakesContext", start_time: float, processes: dict[str, psutil.Process]) -> None:
    """Prints the values from the simulation in a pretty way.

    :param airbrakes: The airbrakes context object.
    :param start_time: The time the simulation started, in seconds from epoch.
    """
    # Print values with multiple print statements
    # The <10 is used to align the values to the left with a width of 10
    # The .2f is used to format the float to 2 decimal places
    print(f"Time since sim start:        {time.time() - start_time:<10.2f} s")
    print(f"State:                       {airbrakes.state.name:<10}")
    print(f"Current speed:               {airbrakes.data_processor.speed:<10.2f} m/s")
    print(f"Max speed so far:            {airbrakes.data_processor.max_speed:<10.2f} m/s")
    print(f"Current altitude:            {airbrakes.data_processor.current_altitude:<10.2f} m")
    print(f"Max altitude so far:         {airbrakes.data_processor.max_altitude:<10.2f} m")
    print(f"Current airbrakes extension: {airbrakes.current_extension:<10}")
    print(f"\n{'='*10} REAL TIME CPU LOAD {'='*14}\n")
    for name, process in processes.items():
        # The < and > are just used to "justify" the text to the left or right, so it looks nice
        # The interval argument, if passed, is blocking, so that's why we put it as None
        print(f"{name:<25} - CPU Usage: {process.cpu_percent(interval=None):>8.2f}%")

    # Move the cursor up 10 lines to overwrite the previous output
    print(MOVE_CURSOR_UP * (10 + len(processes)), end="", flush=True)


def prepare_process_dict(airbrakes: "AirbrakesContext") -> dict[str, psutil.Process]:
    all_processes = {}
    imu_process = airbrakes.imu._data_fetch_process
    log_process = airbrakes.logger._log_process
    current_process = multiprocessing.current_process()
    for p in [imu_process, log_process, current_process]:
        all_processes[p.name] = psutil.Process(p.pid)
    return all_processes
