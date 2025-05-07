"""
File which contains utility functions which can be reused in the simulation.
"""

import random

import numpy as np

from airbrakes.simulation.random_config import RandomAttribute
from airbrakes.simulation.sim_config import SimulationConfig


def update_timestamp(current_timestamp: np.float64, config: SimulationConfig) -> np.float64:
    """
    Updates the current timestamp of the data generator, based off time step defined in config.

    Will also determine if the next timestamp will be a raw packet, estimated packet, or both.
    :param current_timestamp: the current timestamp of the simulation
    :return: the updated current timestamp, rounded to 3 decimals
    """
    # finding whether the raw or estimated data packets have a lower time_step
    lowest_dt = min(config.raw_time_step, config.est_time_step)
    highest_dt = max(config.raw_time_step, config.est_time_step)

    # checks if current time is a multiple of the highest and/or lowest time step
    at_low = any(np.isclose(current_timestamp % lowest_dt, [0, lowest_dt]))
    at_high = any(np.isclose(current_timestamp % highest_dt, [0, highest_dt]))

    # If current timestamp is a multiple of both, the next timestamp will be the
    # current timestamp + the lower time steps
    if all([at_low, at_high]):
        return np.round(current_timestamp + lowest_dt, 3)

    # If timestamp is a multiple of just the lowest time step, the next will be
    # either current + lowest, or the next timestamp that is divisible by the highest
    if at_low and not at_high:
        dt = min(lowest_dt, highest_dt - (current_timestamp % highest_dt))
        return np.round(current_timestamp + dt, 3)

    # If timestamp is a multiple of only the highest time step, the next will
    # always be the next timestamp that is divisible by the lowest
    if at_high and not at_low:
        return np.round(current_timestamp + lowest_dt - (current_timestamp % lowest_dt), 3)

    # This would happen if the input current timestamp is not a multiple of the raw
    # or estimated time steps, or if there is a rounding/floating point error.
    raise ValueError("Could not update timestamp, time stamp is invalid")


def get_random_value(
    value_configs: RandomAttribute, reference_value: np.float64 | None = None
) -> np.float64:
    """
    Gets a random value for the selected identifier, using the standard deviation if given. If a
    reference value is given, assumes a regression model for the RMS of the identifier.

    :param value_configs: the RandomAttribute class containing the randomness properties
    :param reference_value: reference value used if a regression model is used
    :return: float containing a random value for the selected value
    """
    rand_range = value_configs.range
    if value_configs.regression_coefficients is not None:
        coeffs = value_configs.regression_coefficients
        if rand_range is not None:
            range_diff = coeffs[0] * reference_value + coeffs[1]
            rand_range[0] -= range_diff
            rand_range[1] += range_diff
        else:
            rms = coeffs[0] * reference_value + coeffs[1]
            return random.gauss(0, value_configs.std_dev) * rms * np.sqrt(2)

    match value_configs.type:
        case "constant":
            return value_configs.value
        case "uniform":
            return random.uniform(rand_range[0], rand_range[1])
        case "normal":
            if value_configs.mean is not None:
                return random.gauss(value_configs.mean, value_configs.std_dev)
            if value_configs.std_dev is not None:
                return random.gauss(0, value_configs.std_dev)
            raise Exception(f"invalid random config format for {value_configs}")
