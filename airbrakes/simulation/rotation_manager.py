"""
Module that contains methods for rotation operations.
"""

import numpy as np
import numpy.typing as npt
from scipy.spatial.transform import Rotation as R

from airbrakes.constants import GRAVITY_METERS_PER_SECOND_SQUARED, MAX_VELOCITY_THRESHOLD


class RotationManager:
    """
    Manages rotation calculations for rocket orientation.

    This class provides methods to compute and apply various rotation operations, for the purpose of
    generating accurate 6DOF data points for the simulation IMU
    """

    __slots__ = (
        "_azimuth",
        "_last_orientation",
        "_orientation",
        "_wgs_vertical",
        "_zenith",
    )

    def __init__(
        self,
        wgs_vertical: npt.NDArray,
        launch_rod_pitch: np.float64,
        launch_rod_azimuth: np.float64,
    ) -> None:
        """
        Initializes a RotationManager instance with a specified WGS vertical direction vector. This
        serves as the reference direction for rotation operations.

        :param wgs_vertical: the WGS vertical direction vector of the rocket.
        :param launch_rod_pitch: pitch angle of the launch rod, in degrees.
        :param launch_rod_azimuth: the azimuth rotation of the launch rod, in degrees.
        """
        self._wgs_vertical: npt.NDArray = wgs_vertical
        self._zenith: np.float64 = np.float64((launch_rod_pitch * np.pi) / 180)
        self._azimuth: np.float64 = np.float64((launch_rod_azimuth * np.pi) / 180)
        self._last_orientation: R | None = None
        self._orientation: R | None = None
        self.update_orientation(MAX_VELOCITY_THRESHOLD)

    @property
    def gravity_vector(self) -> npt.NDArray:
        return self._orientation.apply([0, 0, -GRAVITY_METERS_PER_SECOND_SQUARED])

    def update_orientation(self, velocity_ratio: np.float64) -> None:
        """
        Updates the baseline vehicle-frame orientation, and all of the vehicle-frame orientations.

        :param velocity_ratio: current vertical velocity of the rocket divided by max velocity
        """
        a = 0.06
        b = -0.69
        c = 2.1
        d = 0.4

        self._zenith = d / (b + np.exp(c * velocity_ratio)) + a

        # We want to convert the azimuth and zenith values into a scipy rotation object

        # Step 1: We have to declare that the orientation of the rocket is vertical
        aligned_orientation = R.align_vectors([self._wgs_vertical], [[0, 0, 1]])[0]

        # Step 2: Get the axis that the zenith rotates around, it changes depending on orientation.
        zenith_rotation_axis = np.array(
            [
                np.abs(self._wgs_vertical[2]),
                np.abs(self._wgs_vertical[0]),
                np.abs(self._wgs_vertical[1]),
            ]
        )

        # Step 3: rotate by zenith
        zenith_rotation = R.from_rotvec(self._zenith * zenith_rotation_axis)

        # Step 4: rotate by azimuth
        azimuth_rotation = R.from_rotvec(self._azimuth * np.array(self._wgs_vertical))

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
        Uses the acceleration due to drag and thrust in Earth frame to find the compensated
        acceleration.

        :param drag_acceleration: scalar value of acceleration due to drag
        :param thrust_acceleration: scalar value of acceleration due to thrust
        :return: the compensated acceleration in the vehicle frame.
        """
        thrust_drag_accel = thrust_acceleration - drag_acceleration
        compensated_accel = self._scalar_to_vector(thrust_drag_accel)
        # if the thrust is non-zero, and this returns a value smaller than gravity, than the rocket
        # is still on the ground. We have to include the acceleration due to the normal force of
        # the ground.
        if (
            thrust_drag_accel <= GRAVITY_METERS_PER_SECOND_SQUARED
            and thrust_acceleration != 0.0
            and drag_acceleration < 1
        ):
            normal_force_vector = np.array([0, 0, GRAVITY_METERS_PER_SECOND_SQUARED])
            rotated_normal_vector = self._orientation.apply(normal_force_vector)

            compensated_accel += rotated_normal_vector
        return compensated_accel

    def calculate_linear_accel(
        self, thrust_acceleration: np.float64, drag_acceleration: np.float64
    ) -> npt.NDArray:
        """
        Uses the acceleration due to drag and thrust in Earth frame to find the linear acceleration.

        :param drag_acceleration: scalar value of acceleration due to drag
        :param thrust_acceleration: scalar value of acceleration due to thrust
        :return: the linear acceleration in vehicle frame
        """
        # gets compensated acceleration
        comp_accel = self.calculate_compensated_accel(thrust_acceleration, drag_acceleration)
        # apply gravity
        gravity_accel_vector = self._orientation.apply([0, 0, GRAVITY_METERS_PER_SECOND_SQUARED])
        return np.array(comp_accel - gravity_accel_vector)

    def calculate_delta_theta(self) -> npt.NDArray:
        """
        Calculates the delta theta in the vehicle frame, with units in radians.

        :return: numpy array containing the delta thetas, in [x, y, z] format, in vehicle frame.
        """
        # first have to take the current orientation and the last orientation, which rotates
        # from Earth frame to vehicle frame, and convert to rotations from vehicle frame to
        # Earth frame.
        imu_adjusted_orientation = self._orientation
        imu_adjusted_last_orientation = self._last_orientation

        # Calculate the relative rotation from the new inverted rotations
        relative_rotation = imu_adjusted_last_orientation * imu_adjusted_orientation.inv()

        # Expresses as a rotation vector
        return relative_rotation.as_rotvec()

    def calculate_rotated_accelerations(self, compensated_acceleration: npt.NDArray) -> npt.NDArray:
        """
        Calculates the rotated acceleration vector with the compensated acceleration. Rotates from
        vehicle frame to Earth frame.

        :param compensated_acceleration: compensated acceleration in the vehicle frame.
        :return: numpy array containing the acceleration vector in Earth frame.
        """
        # inverts the rotation, so it rotates from vehicle frame to Earth frame.
        imu_adjusted_orientation = self._orientation.inv()

        return imu_adjusted_orientation.apply([compensated_acceleration])[0]

    def calculate_imu_quaternions(self) -> npt.NDArray:
        """
        Calculates the quaternion orientation of the rocket.

        :return: numpy array containing the quaternion, in [w, x, y, z] format.
        """
        # flips and inverts the rotation, so that the quaternions are represented
        # accurately, reflecting what the IMU would output.
        imu_alignment = R.align_vectors([[0, 0, 1]], [[0, 0, -1]])[0]
        imu_quaternion_rotation = imu_alignment * self._orientation.inv()

        # returns the rotation as a quaternion
        return imu_quaternion_rotation.as_quat(scalar_first=True)

    def _scalar_to_vector(self, scalar: np.float64) -> npt.NDArray:
        """
        Converts a scalar value to a vector, where it will align with the designated wgs vertical
        vector.

        :param scalar: a float representing the scalar to be converted
        :return: a 3-element numpy array containing the converted vector.
        """
        vector = np.zeros(3)
        # Gets index of non-zero value in the vertical orientation
        index = np.argmax(np.abs(self._wgs_vertical))
        # Place the scalar in the appropriate position, and with the correct sign
        vector[index] = scalar * self._wgs_vertical[index]
        return vector
