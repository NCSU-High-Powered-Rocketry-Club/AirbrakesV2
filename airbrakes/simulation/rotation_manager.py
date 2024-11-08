"""Module that contains methods for rotation operations"""

from collections import deque

import numpy as np
import numpy.typing as npt


class RotationManager:
    """
    Manages rotation calculations for rocket orientation. This class provides
    methods to compute and apply various rotation operations, for the purpose
    of generating accurate 6DOF data points for the simulation IMU
    """

    __slots__ = (
        "_azimuths",
        "_vertical",
        "_zeniths",
    )

    def __init__(
        self, orientation: npt.NDArray, rod_angle_of_attack: np.float64, rod_direction: np.float64
    ) -> None:
        """
        Initializes a RotationManager instance with a specified orientation. This orientation
        serves as the reference direction for rotation operations.

        :param orientation: the vertical orientation of the rocket
        """
        self._vertical: npt.NDArray = orientation
        self._zeniths: deque = deque[(rod_angle_of_attack * np.pi) / 180]
        self._azimuths: deque = deque[(rod_direction * np.pi) / 180]

    def update_orientation(self, time_step: np.float64, vertical_velocity: np.float64) -> None:
        """
        Updates the baseline vehicle-frame orientation, based on how close the velocity
        is to zero. This accounts for the velocity being zero at the start of launch

        :param time_step: how much time has passed between updates
        :param vertical_velocity: current vertical velocity of the rocket
        """
        # we dont want to change angle if in motor burn phase, for simplicity
        if self._zeniths[-1] is not self._zeniths[0] or vertical_velocity >= 100:
            self._zeniths.append(
                (np.pi / 2 - self._zeniths[0]) * np.exp(-0.035 * vertical_velocity)
                + self._zeniths[0]
            )
        _ = time_step
