"""Module for processing IMU data on a higher level."""

from collections import deque

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import ACCELERATION_NOISE_THRESHOLD, Z_DOWN
from utils import deadband


class IMUDataProcessor:
    """
    Performs high level calculations on the data packets received from the IMU. Includes
    calculation the rolling averages of acceleration, maximum altitude so far, etc., from the set of
    data points.
    """

    __slots__ = (
        "_current_altitudes",
        "_current_orientation_quaternions",
        "_data_points",
        "_first_data_point",
        "_gravity_orientation",
        "gravity_upwards",
        "_initial_altitude",
        "_last_data_point",
        "_max_altitude",
        "_max_vertical_velocity",
        "_previous_velocity",
        "_rotated_accelerations",
        "_time_differences",
        "_vertical_velocities",
        "gravity_magnitude",
        "upside_down",
    )

    def __init__(self):
        """
        Initializes the IMUDataProcessor object. It processes data points to calculate various things we need such as
        the maximum altitude, current altitude, speed, etc. All numbers in this class are handled with numpy.

        This class has properties for the maximum altitude, current altitude, speed, and maximum speed of the rocket.

        """
        self._max_altitude: np.float64 = np.float64(0.0)
        self._vertical_velocities: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._max_vertical_velocity: np.float64 = np.float64(0.0)
        self._previous_velocity: npt.NDArray[np.float64] = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._last_data_point: EstimatedDataPacket | None = None
        self._first_data_point: EstimatedDataPacket | None = None
        self._current_orientation_quaternions: npt.NDArray[np.float64] = None
        self._rotated_accelerations: list[npt.NDArray[np.float64]] = [np.array([0.0]), np.array([0.0]), np.array([0.0])]
        self._data_points: list[EstimatedDataPacket] = []
        self._time_differences: npt.NDArray[np.float64] | None = None
        self._gravity_orientation: npt.NDArray[np.float64] | None = None
        self._gravity_upwards : np.float64 | None = None
        self.gravity_magnitude : np.float64 | None = None

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"max_altitude={self.max_altitude}, "
            f"current_altitude={self.current_altitude}, "
            f"speed={self.vertical_velocity}, "
            f"max_speed={self.max_vertical_velocity}, "
        )

    @property
    def max_altitude(self) -> float:
        """
        Returns the highest altitude (zeroed out) attained by the rocket for the entire flight
        so far, in meters.
        """
        return float(self._max_altitude)

    @property
    def current_altitude(self) -> float:
        """Returns the altitudes of the rocket (zeroed out) from the data points, in meters."""
        return float(self._current_altitudes[-1])

    @property
    def vertical_velocity(self) -> float:
        """The current vertical velocity of the rocket in m/s. Calculated by integrating the linear acceleration."""
        return float(self._vertical_velocities[-1])

    @property
    def max_vertical_velocity(self) -> float:
        """The maximum vertical velocity the rocket has attained during the flight, in m/s."""
        return float(self._max_vertical_velocity)

    def update(self, data_points: list[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. This will recompute all information such as altitude,
        speed, etc.
        :param data_points: A list of EstimatedDataPacket objects to process
        """
        # If the data points are empty, we don't want to try to process anything
        if not data_points:
            return

        self._data_points = data_points

        # If we don't have a last data point, we can't calculate the time differences needed
        # for speed calculation:
        if self._last_data_point is None:
            # setting last data point as the first element, makes it so that the time diff
            # automatically becomes 0, and the speed becomes 0
            self._last_data_point = self._data_points[0]
            # This is us getting the rocket's initial orientation
            self._current_orientation_quaternions = np.array(
                [
                    self._last_data_point.estOrientQuaternionW,
                    self._last_data_point.estOrientQuaternionX,
                    self._last_data_point.estOrientQuaternionY,
                    self._last_data_point.estOrientQuaternionZ,
                ]
            )

            # We also get the initial gravity vector to determine which direction is up
            self._gravity_orientation = np.array(
                [
                    self._last_data_point.estGravityVectorX,
                    self._last_data_point.estGravityVectorY,
                    self._last_data_point.estGravityVectorZ,
                ]
            )
            # finding max of absolute value of gravity vector, and finding index
            absolute_gravity_vector = np.abs(self._gravity_orientation)
            self._gravity_upwards = absolute_gravity_vector.index(max(absolute_gravity_vector))

            self.gravity_magnitude = np.linalg.norm(self._gravity_orientation)
            if self._gravity_orientation[self._gravity_upwards] < 0:
                gravity_magnitude = gravity_magnitude*-1 


        self._time_differences = self._calculate_time_differences()

        self._rotated_accelerations = self._calculate_rotated_accelerations()
        self._vertical_velocities = self._calculate_velocities()
        self._max_vertical_velocity = max(self._vertical_velocities.max(), self._max_vertical_velocity)

        self._current_altitudes = self._calculate_current_altitudes()
        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        # Store the last data point for the next update
        self._last_data_point = data_points[-1]

    def get_processed_data_packets(self) -> deque[ProcessedDataPacket]:
        """
        Processes the data points and returns a deque of ProcessedDataPacket objects. The length
        of the deque should be the same as the length of the list of estimated data packets most
        recently passed in by update()

        :return: A deque of ProcessedDataPacket objects.
        """
        return deque(
            ProcessedDataPacket(
                current_altitude=current_alt,
                speed=speed,
            )
            for current_alt, speed in zip(self._current_altitudes, self._vertical_velocities, strict=False)
        )

    def _calculate_current_altitudes(self) -> npt.NDArray[np.float64]:
        """
        Calculates the current altitudes, by zeroing out the initial altitude.
        :return: A numpy array of the current altitudes of the rocket at each data point
        """
        # Get the pressure altitudes from the data points
        altitudes = np.array([data_point.estPressureAlt for data_point in self._data_points], dtype=np.float64)
        # Zero the altitude only once, during the first update:
        if self._initial_altitude is None:
            self._initial_altitude = np.mean(altitudes)
        # Zero out the initial altitude
        return altitudes - self._initial_altitude

    def _calculate_rotated_accelerations(self) ->  list[npt.NDArray[np.float64]]:
        """
        Calculates the rotated acceleration vector. Converts gyroscope data into a delta quaternion, and adds
        onto the last quaternion. Will most likely be replaced by IMU quaternion data in the future, this
        is a work-around due to bad datasets.

        :return: numpy list of rotated acceleration vector [x,y,z]
        """

        accel_rotated_quats = [
            np.zeros(len(self._data_points)),
            np.zeros(len(self._data_points)),
            np.zeros(len(self._data_points))
        ]

        # Iterates through the data points and time differences between the data points
        for i, (data_point, dt) in enumerate(zip(self._data_points, self._time_differences, strict=False)):
            # Accelerations are in m/s^2
            x_accel = data_point.estCompensatedAccelX
            y_accel = data_point.estCompensatedAccelY
            z_accel = data_point.estCompensatedAccelZ
            # Angular rates are in rads/s
            gyro_x = data_point.estAngularRateX
            gyro_y = data_point.estAngularRateY
            gyro_z = data_point.estAngularRateZ

            # If we are missing the data points, then say we didn't rotate
            if not any([x_accel, y_accel, z_accel, gyro_x, gyro_y, gyro_z]):
                return [np.array([0.0]), np.array([0.0]), np.array([0.0])]

            # rotation matrix for rate of change quaternion, with epsilon and K used to drive the norm to 1
            # explained at the bottom of this page: https://www.mathworks.com/help/aeroblks/6dofquaternion.html
            gyro_to_quaternion_matrix = np.array(
                [
                    [0, -gyro_x, -gyro_y, -gyro_z],
                    [gyro_x, 0, gyro_z, -gyro_y],
                    [gyro_y, -gyro_z, 0, gyro_x],
                    [gyro_z, gyro_y, -gyro_x, 0],
                ]
            )

            deltaQuat = 0.5 * np.matmul(
                gyro_to_quaternion_matrix, np.transpose(self._current_orientation_quaternions)
            )
            # Updates quaternion by adding delta quaternion, and rotates acceleration vector
            self._current_orientation_quaternions = self._current_orientation_quaternions + np.transpose(deltaQuat) * dt
            # Normalize quaternion
            self._current_orientation_quaternions = self._current_orientation_quaternions / np.linalg.norm(
                self._current_orientation_quaternions
            )
            # Rotate acceleration by quaternion
            accelQuat = np.array([0, x_accel, y_accel, z_accel])
            accelRotatedQuat = self._multiply_quaternions(
                self._multiply_quaternions(self._current_orientation_quaternions, accelQuat),
                self._calculate_quaternion_conjugate(self._current_orientation_quaternions),
            )

            # Adds the accelerations to our list of rotated accelerations
            accel_rotated_quats[0][i] = accelRotatedQuat[1]
            accel_rotated_quats[1][i] = accelRotatedQuat[2]
            accel_rotated_quats[2][i] = accelRotatedQuat[3]

        return accel_rotated_quats

    def _calculate_velocities(self) -> npt.NDArray[np.float64]:
        """
        Calculates the speed of the rocket based on the linear acceleration. Integrates the
        linear acceleration to get the speed.
        :param data_points: A sequence of EstimatedDataPacket objects to process
        :return: A numpy array of the speed of the rocket at each data point
        """
        # Get the deadbanded accelerations in the x, y, and z directions
        # TODO: we need to deadband the acceleration
        x_accelerations, y_accelerations, z_accelerations = self._rotated_accelerations
        # Get the time differences between each data point and the previous data point

        # We store the previous calculated velocity vectors, so that our speed
        # doesn't show a jump, e.g. after motor burn out.
        previous_vel_x, previous_vel_y, previous_vel_z = self._previous_velocity

        # We integrate each of the components of the acceleration to get the velocity
        velocities_x = previous_vel_x + np.cumsum((x_accelerations * Z_DOWN[0]) * self._time_differences)
        velocities_y = previous_vel_y + np.cumsum((y_accelerations * Z_DOWN[1]) * self._time_differences)
        velocities_z = previous_vel_z + np.cumsum((z_accelerations * Z_DOWN[2]) * self._time_differences)

        # adding gravity into the acceleration vector based off of the upwards direction
        velocities_vector = [velocities_x,velocities_y,velocities_z]
        velocities_vector[self._gravity_upwards] = velocities_vector[self._gravity_upwards] + self.gravity_magnitude

        # Store the last calculated velocity vectors
        self._previous_velocity = (velocities_vector[0][-1], velocities_vector[1][-1], velocities_vector[2][-1])

        # Gets the vertical velocity
        vertical_velocites = velocities_vector[self._gravity_upwards]
        return vertical_velocites

    def _calculate_time_differences(self) -> npt.NDArray[np.float64]:
        """
        Calculates the time difference between each data point and the previous data point. This cannot
        be called on the first update as _last_data_point is None. This method is cached and time
        diff is only computed once for a set of data points.
        :return: A numpy array of the time difference between each data point and the previous data point.
        """
        # calculate the time differences between each data point
        # We are converting from ns to s, since we don't want to have a speed in m/ns^2
        # We are using the last data point to calculate the time difference between the last data point from the
        # previous loop, and the first data point from the current loop
        return np.diff([data_point.timestamp for data_point in [self._last_data_point, *self._data_points]]) * 1e-9

    def _get_deadbanded_accelerations(
        self,
    ) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        """
        Gets the deadbanded accelerations in the x, y, and z directions.
        :return: A tuple of numpy arrays of the deadbanded accelerations in the x, y, and z directions.
        """
        # Deadbands the accelerations in the x, y, and z and creates the numpy arrays via list comprehension
        # As it turns out, list comprehensions are significantly faster than appending to a list in a for loop or
        # pre-allocating a numpy array and filling it in a for loop.
        # We use linearAcceleration because we don't want gravity to affect our calculations for speed
        x_accelerations = np.array(
            [deadband(data_point.estLinearAccelX, ACCELERATION_NOISE_THRESHOLD) for data_point in self._data_points],
            dtype=np.float64,
        )
        y_accelerations = np.array(
            [deadband(data_point.estLinearAccelY, ACCELERATION_NOISE_THRESHOLD) for data_point in self._data_points],
            dtype=np.float64,
        )
        z_accelerations = np.array(
            [deadband(data_point.estLinearAccelZ, ACCELERATION_NOISE_THRESHOLD) for data_point in self._data_points],
            dtype=np.float64,
        )

        return x_accelerations, y_accelerations, z_accelerations

    def _multiply_quaternions(self, q1: npt.NDArray[np.float64], q2: npt.NDArray[np.float64]):
        """
        Calculates the quaternion multiplication. quaternion multiplication is not commutative, e.g. q1q2 =/= q2q1

        :param q1: numpy array with the first quaternion in row form
        :param q2: numpy array with the second quaternion in row form

        :return: numpy array with the multiplied quaternion
        """
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2

        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
        return np.array([w, x, y, z])

    def _calculate_quaternion_conjugate(self, q: npt.NDArray[np.float64]):
        """
        Calculates the conjugate of a quaternion

        :param q1: numpy array with a quaternion in row form

        :return: numpy array with the quaternion conjugate
        """
        w, x, y, z = q
        return np.array([w, -x, -y, -z])
