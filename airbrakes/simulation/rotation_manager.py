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
        self.update_orientation(0, 0)

    @property
    def gravity_vector(self) -> npt.NDArray:
        return self._orientation.apply([0, 0, -GRAVITY])

    def update_orientation(self, time_step: np.float64, velocity_ratio: np.float64) -> None:
        """
        Updates the baseline vehicle-frame orientation, and all of the vehicle-frame
        orientations

        :param time_step: how much time has passed between updates
        :param velocity_ratio: current vertical velocity of the rocket divided by max velocity
        """
        if velocity_ratio == 0.0:
            scale_factor = 0.0
        else:
            scale_factor = np.sin(self._zenith) * time_step / abs(velocity_ratio * 10)
        self._zenith = self._zenith + scale_factor * (np.pi / 2 - self._zenith)

        # We want to convert the azimuth and zenith values into a scipy rotation object

        # Step 1: We have to declare that the orientation of the rocket is vertical
        aligned_orientation = R.align_vectors([self._vertical], [[0, 0, 1]])[0]

        # Step 2: Tilt by the zenith angle to adjust pitch away from vertical
        tilt_rotation = R.from_rotvec(self._zenith * np.array([1, 0, 0]))

        # Step 3: Rotate around the vertical by azimuth to set the compass direction of the tilt
        azimuth_rotation = R.from_rotvec(self._azimuth * np.array([0, 0, -1]))

        # Step 4: Combined rotation: aligned orientation, followed by azimuth and zenith rotations
        orientation = azimuth_rotation * tilt_rotation * aligned_orientation

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
        # if the thrust is non-zero, and this returns a value smaller than gravity, than the rocket
        # is still on the ground. We have to include the acceleration due to the normal force of
        # the ground.
        compensated_accel = self._scalar_to_vector(thrust_drag_accel)
        if thrust_drag_accel <= GRAVITY and thrust_drag_accel != 0.0:
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
        gravity_accel_vector = self._orientation.apply([0, 0, -GRAVITY])
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
        imu_alignment_rotation = R.align_vectors([[0, 0, 1]], [[0, 0, -1]])[0]
        imu_adjusted_orientation = imu_alignment_rotation * self._orientation

        # convert to quaternion
        return imu_adjusted_orientation.as_quat(scalar_first=True)

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
