def convert_to_nanoseconds(value) -> int:
    if isinstance(value, float):
        # Convert seconds to nanoseconds
        nanoseconds = value * 1e9
        return int(nanoseconds)  # Convert to integer if needed
    return value  # Assume that it is in nanoseconds


def convert_to_float(value) -> float | None:
    try:
        float_value = float(value)  # Attempt to convert to float
        return float_value
    except (ValueError, TypeError):
        return None  # Return None if the conversion fails
