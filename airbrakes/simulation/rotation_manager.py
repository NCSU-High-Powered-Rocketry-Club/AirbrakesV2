"""Module that contains methods for rotation operations"""

import numpy as np
import numpy.typing as npt


class RotationManager:
    """
    Manages rotation calculations for rocket orientation. This class provides
    methods to compute and apply various rotation operations, for the purpose
    of generating accurate 6DOF data points for the simulation IMU
    """

    __slots__ = (
        "_azimuth",
        "_vertical",
        "_zenith",
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
        self._zenith: np.float64 = (rod_angle_of_attack * np.pi) / 180
        self._azimuth: np.float64 = (rod_direction * np.pi) / 180

    def update_orientation(self, time_step: np.float64) -> None:
        """
        Updates the baseline vehicle-frame orientation

        :param time_step: how much time has passed between updates
        :param apogee_progress: current altitude divided by the target apogee
        """
