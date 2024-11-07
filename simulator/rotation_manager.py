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
        "_vertical",
    )

    def __init__(
            self,
            orientation: npt.NDArray,
            rod_angle_of_attack: np.float64,
            
            ) -> None:
        """
        Initializes a RotationManager instance with a specified orientation. This orientation
        serves as the reference direction for rotation operations.

        :param orientation: the vertical orientation of the rocket
        """
        self._vertical = orientation



