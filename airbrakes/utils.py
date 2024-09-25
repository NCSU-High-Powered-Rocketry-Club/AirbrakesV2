"""File which contains a few basic utility functions which can be reused in the project."""


def convert_to_nanoseconds(value: float) -> int:
    """Converts seconds to nanoseconds, if `value` is in float."""
    if isinstance(value, float):
        # Convert seconds to nanoseconds
        nanoseconds = value * 1e9
        return int(nanoseconds)  # Convert to integer if needed
    return value  # Assume that it is in nanoseconds


def convert_to_float(value) -> float | None:
    """Converts a value to a float, returning None if the conversion fails."""
    try:
        return float(value)  # Attempt to convert to float
    except (ValueError, TypeError):
        return None  # Return None if the conversion fails
