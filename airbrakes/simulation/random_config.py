"""Module containing config settings for randomness in the simulation"""

from copy import deepcopy
from enum import Enum

import numpy as np
import numpy.typing as npt


class RandomType(Enum):
    """Enum that designates the type of randomness to apply"""

    CONSTANT = "constant"
    """a constant value, no randomness. Constructed with only type and value arguments"""
    UNIFORM = "uniform"
    """uniform distribution. Construct with type and range, reg coeff's optional"""
    NORMAL = "normal"
    """normal distribution. Construct with type and std_dev, mean, range, and regression
    coefficients optional"""


class RandomAttribute:
    """
    Randomness settings for an individual attribute
    """

    def __init__(
        self,
        type: RandomType,
        value: np.float64 | None = None,
        range: npt.NDArray[np.float64] | None = None,
        std_dev: np.float64 | None = None,
        mean: np.float64 | None = None,
        regression_coefficients: npt.NDArray[np.float64] | None = None,
    ):
        self.type = type
        self.value = value
        self.range = range
        self.std_dev = std_dev
        self.mean = mean
        self.regression_coefficients = regression_coefficients


class RandomConfig:
    """
    Configuration settings for the randomness in the simulation.
    """

    def __init__(
        self,
        acceleration_noise_coefficients: RandomAttribute,
    ):
        # acceleration noise is calculated with a linear equation dependent on the vertical
        # component of acceleration. The first value is m, the second value is b, in
        # the format y=mx+b, third value is standard deviation
        self.acceleration_noise_coefficients = acceleration_noise_coefficients


def create_modified_config(overrides: dict) -> RandomConfig:
    """
    Modifies the default configuration settings by overriding with specified values

    :param overrides: A dictionary of parameters to override.
    :return: A RandomConfig object containing modified configuration values
    """
    base_config = deepcopy(DEFAULT_RAND_CONFIG)
    for key, value in overrides.items():
        setattr(base_config, key, value)
    return base_config


DEFAULT_RAND_CONFIG = RandomConfig(
    acceleration_noise_coefficients=RandomAttribute(
        RandomType.NORMAL, std_dev=1, regression_coefficients=[0.0403, 0.0505]
    ),
)

SUB_SCALE_RAND_CONFIG = create_modified_config(
    {
        "acceleration_noise_coefficients": RandomAttribute(
            RandomType.NORMAL, std_dev=1, regression_coefficients=[0.0258, 0.01875]
        ),
    }
)
