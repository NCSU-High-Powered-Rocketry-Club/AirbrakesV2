"""File which contains a few basic utility functions which can be reused in the project."""

import time
from typing import TYPE_CHECKING

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


def update_display(airbrakes: "AirbrakesContext", start_time: float):
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

    # Move the cursor up 7 lines to overwrite the previous output
    print(MOVE_CURSOR_UP * 7, end="", flush=True)
