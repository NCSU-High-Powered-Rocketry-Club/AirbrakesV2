"""Module that contains methods for rotation operations"""

import numpy as np
import numpy.typing as npt
from scipy.spatial.transform import Rotation as R

from constants import GRAVITY


class RotationManager:
    """
    Manages rotation calculations for rocket orientation. This class provides
    methods to compute and apply various rotation operations, for the purpose
    of generating accurate 6DOF data points for the simulation IMU
    """

    __slots__ = (
        "_azimuth",
        "_formula_consts",
        "_last_orientation",
        "_orientation",
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
        self._zenith: np.float64 = np.float64((rod_angle_of_attack * np.pi) / 180)
        self._azimuth: np.float64 = np.float64((rod_direction * np.pi) / 180)
        self._last_orientation: R | None = None
        self._orientation: R | None = None
        self._formula_consts: npt.NDArray = self._initialize_rotation_formula()
        self.update_orientation(1)

    @property
    def gravity_vector(self) -> npt.NDArray:
        return self._orientation.apply([0, 0, -GRAVITY])

    def _initialize_rotation_formula(self) -> np.float64:
        """
        Initializes the formula for rotation. Returns the shift of the function. Is constant
        for the rest of the flight.
        :return: the shift and initial angle of the function.
        """
        # initializes vector with small step values, the shift is always below 0.1
        # for inital rod angles below 45 degrees
        dx = 0.00001
        xvec = np.arange(dx, 0.1, dx)
        # this graph is zenith versus v/vmax
        no_shift = (-xvec + 1) / (15 * xvec) + self._zenith
        # finding the index where no_shift is closest to pi/2
        closest_index = np.argmin(np.abs(no_shift - np.pi / 2))
        return np.array([closest_index * dx, self._zenith])  # returns the shift and zenith

    def update_orientation(self, velocity_ratio: np.float64) -> None:
        """
        Updates the baseline vehicle-frame orientation, and all of the vehicle-frame
        orientations

        :param velocity_ratio: current vertical velocity of the rocket divided by max velocity
        """
        # splitting up the function into two parts
        devisor = 15 * (self._formula_consts[0] + 1) * (velocity_ratio + self._formula_consts[0])
        self._zenith = (-velocity_ratio + 1) / devisor + self._formula_consts[1]

        # We want to convert the azimuth and zenith values into a scipy rotation object

        # Step 1: We have to declare that the orientation of the rocket is vertical
        aligned_orientation = R.align_vectors([self._vertical], [[0, 0, 1]])[0]

        # Step 2: Get the axis that the zenith rotates around, it changes depending on orientation.
        zenith_rotation_axis = np.array(
            [
                np.abs(self._vertical[2]),
                np.abs(self._vertical[0]),
                np.abs(self._vertical[1]),
            ]
        )

        # Step 3: rotate by zenith
        zenith_rotation = R.from_rotvec(self._zenith * zenith_rotation_axis)

        # Step 4: rotate by azimuth
        azimuth_rotation = R.from_rotvec(self._azimuth * np.array(self._vertical))

        # Step 5: Combined rotation: aligned orientation, azimuth rotation, and zenith rotation
        orientation = azimuth_rotation * zenith_rotation * aligned_orientation

        # updating last orientation
        self._last_orientation = (
            orientation if self._last_orientation is None else self._orientation
        )
        self._orientation = orientation

    def calculate_compensated_accel(
        self, thrust_acceleration: np.float64, drag_acceleration: np.float64
    ) -> npt.NDArray:
        """
        Uses the acceleration due to drag and thrust to find the compensated acceleration

        :param drag_acceleration: scalar value of acceleration due to drag
        :param thrust_acceleration: scalar value of acceleration due to thrust

        :return: the compensated acceleration in the vehicle frame of reference
        """
        thrust_drag_accel = thrust_acceleration - drag_acceleration
        compensated_accel = self._scalar_to_vector(thrust_drag_accel)
        # if the thrust is non-zero, and this returns a value smaller than gravity, than the rocket
        # is still on the ground. We have to include the acceleration due to the normal force of
        # the ground.
        if thrust_drag_accel <= GRAVITY and thrust_acceleration != 0.0 and drag_acceleration < 1:
            normal_force_vector = np.array([0, 0, GRAVITY])
            rotated_normal_vector = self._orientation.apply(normal_force_vector)

            compensated_accel += rotated_normal_vector
        return compensated_accel

    def calculate_linear_accel(
        self, thrust_acceleration: np.float64, drag_acceleration: np.float64
    ) -> npt.NDArray:
        """
        Uses the compensated acceleration to find the linear acceleration

        :param drag_acceleration: scalar value of acceleration due to drag
        :param thrust_acceleration: scalar value of acceleration due to thrust

        :return: the linear acceleration in the vehicle frame of reference
        """
        comp_accel = self.calculate_compensated_accel(thrust_acceleration, drag_acceleration)
        # apply gravity
        gravity_accel_vector = self._orientation.apply([0, 0, GRAVITY])
        return np.array(comp_accel - gravity_accel_vector)

    def calculate_delta_theta(self) -> npt.NDArray:
        """
        Calculates the delta theta in the vehicle frame of reference, with units in
        radians.

        :return: numpy array containing the delta thetas, in [x, y, z] format.
        """
        # first have to take the current orientation and the last orientation that is in
        # Earth -> vehicle reference and convert to vehicle -> Earth reference
        imu_adjusted_orientation = self._orientation.inv()
        imu_adjusted_last_orientation = self._last_orientation.inv()

        # Calculate the relative rotation from last orientation to the current orientation
        relative_rotation = imu_adjusted_last_orientation.inv() * imu_adjusted_orientation

        # Converts the relative rotation to a rotation vector
        return relative_rotation.as_rotvec()

    def calculate_rotated_accelerations(self, compensated_acceleration: npt.NDArray) -> np.float64:
        """
        Calculates the rotated acceleration vector with the compensated acceleration. Rotates from
        vehicle frame of reference to Earth frame of reference.

        :param compensated_acceleration: compensated acceleration in the vehicle-frame reference.

        :return: float containing vertical acceleration with respect to Earth.
        """
        # rotation needed to align the IMU
        imu_adjusted_orientation = self._orientation.inv()

        return imu_adjusted_orientation.apply([compensated_acceleration])[0]

    def calculate_imu_quaternions(self) -> npt.NDArray:
        """
        Adjusts the given orientation to align with the IMU's reference frame, where
        [0, 0, -1] is vertical, and returns a quaternions.

        :param orientation: A scipy Rotation object representing the current orientation.

        :return: A quaternion adjusted to the IMU's frame.
        """
        # rotation needed to align the IMU
        imu_alignment = R.align_vectors([[0, 0, 1]], [[0, 0, -1]])[0]
        imu_quaternion_rotation = imu_alignment * self._orientation.inv()

        # convert to quaternion
        return imu_quaternion_rotation.as_quat(scalar_first=True)

    def _scalar_to_vector(self, scalar: np.float64) -> npt.NDArray:
        """
        Converts a scalar value to a vector, where it will align with the vertical orientation.

        :param scalar: a float representing the scalar to be converted

        :return: a 3-element numpy array containing the converted vector.
        """
        vector = np.zeros(3)
        # Gets index of non-zero value in the vertical orientation
        index = np.argmax(np.abs(self._vertical))
        # Place the scalar in the appropriate position, and with the correct sign
        vector[index] = scalar * self._vertical[index]
        return vector