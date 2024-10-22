"""Module for processing IMU data on a higher level."""

from collections import deque

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import ACCELERATION_NOISE_THRESHOLD
from utils import deadband


class IMUDataProcessor:
    """
    Performs high level calculations on the data packets received from the IMU. Includes
    calculation the rolling averages of acceleration, maximum altitude so far, etc., from the set of
    data points.
    """

    __slots__ = (
        "_current_altitudes",
        "_data_points",
        "_first_data_point",
        "_initial_altitude",
        "_last_data_point",
        "_max_altitude",
        "_max_speed",
        "_previous_velocity",
        "_quat",
        "_rotated_accel",
        "_speeds",
        "upside_down",
        "_time_diff",
    )

    def __init__(self, upside_down: bool = False):
        """
        Initializes the IMUDataProcessor object. It processes data points to calculate various things we need such as
        the maximum altitude, current altitude, speed, etc. All numbers in this class are handled with numpy.

        This class has properties for the maximum altitude, current altitude, speed, and maximum speed of the rocket.

        :param upside_down: Whether the rocket is upside down or not.
        """
        self.upside_down = upside_down

        self._max_altitude: np.float64 = np.float64(0.0)
        self._speeds: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._max_speed: np.float64 = np.float64(0.0)
        self._previous_velocity: npt.NDArray[np.float64] = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._last_data_point: EstimatedDataPacket | None = None
        self._first_data_point: EstimatedDataPacket | None = None
        self._quat: npt.NDArray[np.float64] = None
        self._rotated_accel: npt.NDArray[np.float64] = None
        self._data_points: list[EstimatedDataPacket] = []
        self._time_diff: npt.NDArray[np.float64] | None = None

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"max_altitude={self.max_altitude}, "
            f"current_altitude={self.current_altitude}, "
            f"speed={self.speed}, "
            f"max_speed={self.max_speed}, "
            f"rotated_accel={self.rotated_accel},)"
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
    def speed(self) -> float:
        """The current speed of the rocket in m/s. Calculated by integrating the linear acceleration."""
        return float(self._speeds[-1])

    @property
    def max_speed(self) -> float:
        """The maximum speed the rocket has attained during the flight, in m/s."""
        return float(self._max_speed)

    @property
    def rotated_accel(self) -> npt.NDArray[np.float64]:
        """the rotated compensated acceleration vectors with respect to Earth frame of reference"""
        return self._rotated_accel

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
            self._quat = np.array(
                [
                    self._last_data_point.estOrientQuaternionW,
                    self._last_data_point.estOrientQuaternionX,
                    self._last_data_point.estOrientQuaternionY,
                    self._last_data_point.estOrientQuaternionZ,
                ]
            )

        self._speeds = self._calculate_speeds()
        self._max_speed = max(self._speeds.max(), self._max_speed)

        self._current_altitudes = self._calculate_current_altitudes()
        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        # Rotate compensated acceleration vector to Earth frame of reference
        self._rotated_accel = self._calculate_rotations()

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
            for current_alt, speed in zip(self._current_altitudes, self._speeds, strict=False)
        )

    def get_time_differences(self) -> npt.NDArray[np.float64]:
        """Returns the time difference of the data points."""
        return self._time_diff

    def reset_time_diff(self):
        """Resets the time difference once update() is called."""
        self._time_diff = None

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

    def _calculate_rotations(self) -> npt.NDArray[np.float64]:
        """
        Calculates the rotated acceleration vector. Converts gyroscope data into a delta quaternion, and adds
        onto the last quaternion. Will most likely be replaced by IMU quaternion data in the future, this
        is a work-around due to bad datasets.

        :return: numpy list of rotated acceleration vector [x,y,z]
        """

        time_diffs = self._get_time_differences()

        for dp, dt in zip(self._data_points, time_diffs, strict=False):
            compx = dp.estCompensatedAccelX
            compy = dp.estCompensatedAccelY
            compz = dp.estCompensatedAccelZ
            gyrox = dp.estAngularRateX
            gyroy = dp.estAngularRateY
            gyroz = dp.estAngularRateZ

            if not any([compx, compy, compz, gyrox, gyroy, gyroz]):
                return np.array([0.0, 0.0, 0.0])

            # rotation matrix for rate of change quaternion, with epsilon and K used to drive the norm to 1
            # explained at the bottom of this page: https://www.mathworks.com/help/aeroblks/6dofquaternion.html
            m = np.array(
                [
                    [0, -gyrox, -gyroy, -gyroz],
                    [gyrox, 0, gyroz, -gyroy],
                    [gyroy, -gyroz, 0, gyrox],
                    [gyroz, gyroy, -gyrox, 0],
                ]
            )
            epsilon = 1 - ((self._quat[0] ** 2) + (self._quat[1] ** 2) + (self._quat[2] ** 2) + (self._quat[3] ** 2))
            K = 5.0
            deltaQuat = 0.5 * np.matmul(m, np.transpose(self._quat)) + K * epsilon * np.transpose(self._quat)

            # updates quaternion by adding delta quaternion, and rotates acceleration vector
            self._quat = self._quat + np.transpose(deltaQuat) * dt
            # normalize quaternion
            self._quat = self._quat / np.linalg.norm(self._quat)
            # rotate acceleration by quaternion
            accelQuat = np.array([0, compx, compy, compz])
            accelRotatedQuat = self._quatmultiply(self._quatmultiply(self._quat, accelQuat), self._quatconj(self._quat))

        return np.array([accelRotatedQuat[1], accelRotatedQuat[2], accelRotatedQuat[3]])

    def _quatmultiply(self, q1: npt.NDArray[np.float64], q2: npt.NDArray[np.float64]):
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

    def _quatconj(self, q: npt.NDArray[np.float64]):
        """
        Calculates the conjugate of a quaternion

        :param q1: numpy array with a quaternion in row form

        :return: numpy array with the quaternion conjugate
        """
        w, x, y, z = q
        return np.array([w, -x, -y, -z])

    def _calculate_speeds(self) -> npt.NDArray[np.float64]:
        """
        Calculates the speed of the rocket based on the linear acceleration. Integrates the
        linear acceleration to get the speed.
        :param data_points: A sequence of EstimatedDataPacket objects to process
        :return: A numpy array of the speed of the rocket at each data point
        """
        # Get the deadbanded accelerations in the x, y, and z directions
        x_accelerations, y_accelerations, z_accelerations = self._get_deadbanded_accelerations()
        # Get the time differences between each data point and the previous data point
        time_differences = self._get_time_differences()

        # We store the previous calculated velocity vectors, so that our speed
        # doesn't show a jump, e.g. after motor burn out.
        previous_vel_x, previous_vel_y, previous_vel_z = self._previous_velocity

        # We integrate each of the components of the acceleration to get the velocity
        velocities_x: np.array = previous_vel_x + np.cumsum(x_accelerations * time_differences)
        velocities_y: np.array = previous_vel_y + np.cumsum(y_accelerations * time_differences)
        velocities_z: np.array = previous_vel_z + np.cumsum(z_accelerations * time_differences)

        # Store the last calculated velocity vectors
        self._previous_velocity = (velocities_x[-1], velocities_y[-1], velocities_z[-1])

        # All the speeds gotten as the magnitude of the velocity vector at each point
        return np.sqrt(velocities_x**2 + velocities_y**2 + velocities_z**2)

    def _get_time_differences(self) -> npt.NDArray[np.float64]:
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
        if self._time_diff is None:
            self._time_diff = np.diff([data_point.timestamp for data_point in [self._last_data_point, *self._data_points]]) * 1e-9
        return self._time_diff

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
