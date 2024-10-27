"""Module for processing IMU data on a higher level."""

from collections import deque

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import ACCELERATION_NOISE_THRESHOLD, GRAVITY
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
        "_data_packets",
        "_first_data_packet",
        "_gravity_direction",
        "_gravity_orientation",
        "_gravity_upwards_index",
        "_initial_altitude",
        "_last_data_packet",
        "_max_altitude",
        "_max_vertical_velocity",
        "_previous_vertical_velocity",
        "_rotated_accelerations",
        "_time_differences",
        "_vertical_velocities",
    )

    def __init__(self):
        """
        Initializes the IMUDataProcessor object. It processes data points to calculate various things we need such as
        the maximum altitude, current altitude, velocity, etc. All numbers in this class are handled with numpy.

        This class has properties for the maximum altitude, current altitude, velocity, and
        maximum velocity of the rocket.
        """
        self._max_altitude: np.float64 = np.float64(0.0)
        self._vertical_velocities: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._max_vertical_velocity: np.float64 = np.float64(0.0)
        self._previous_vertical_velocity: np.float64 = np.float64(0.0)
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._last_data_packet: EstimatedDataPacket | None = None
        self._first_data_packet: EstimatedDataPacket | None = None
        self._current_orientation_quaternions: npt.NDArray[np.float64] | None = None
        self._rotated_accelerations: list[npt.NDArray[np.float64]] = [np.array([0.0]), np.array([0.0]), np.array([0.0])]
        self._data_packets: list[EstimatedDataPacket] = []
        self._time_differences: npt.NDArray[np.float64] = np.array([0.0])
        self._gravity_orientation: npt.NDArray[np.float64] | None = None
        self._gravity_upwards_index: int | None = 0
        self._gravity_direction: np.float64 | None = None

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"max_altitude={self.max_altitude}, "
            f"current_altitude={self.current_altitude}, "
            f"velocity={self.vertical_velocity}, "
            f"max_velocity={self.max_vertical_velocity}, "
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

    def update(self, data_packets: list[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. This will recompute all information such as altitude,
        velocity, etc.
        :param data_packets: A list of EstimatedDataPacket objects to process
        """
        # If the data points are empty, we don't want to try to process anything
        if not data_packets:
            return

        self._data_packets = data_packets

        # If we don't have a last data point, we can't calculate the time differences needed
        # for velocity calculation:
        if self._last_data_packet is None:
            self._first_update()

        self._time_differences = self._calculate_time_differences()

        self._rotated_accelerations = self._calculate_rotated_accelerations()
        self._vertical_velocities = self._calculate_vertical_velocity()
        self._max_vertical_velocity = max(self._vertical_velocities.max(), self._max_vertical_velocity)

        self._current_altitudes = self._calculate_current_altitudes()
        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        # Store the last data point for the next update
        self._last_data_packet = data_packets[-1]

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
                vertical_velocity=vertical_velocity,
                vertical_acceleration=vertical_acceleration,
                time_since_last_data_packet=time_since_last_data_packet,
            )
            for (
                current_alt,
                vertical_velocity,
                vertical_acceleration,
                time_since_last_data_packet,
            ) in zip(
                self._current_altitudes,
                self._vertical_velocities,
                self._rotated_accelerations[self._gravity_upwards_index],
                self._time_differences,
                strict=True,
            )
        )

    @staticmethod
    def _multiply_quaternions(
        first_quaternion: npt.NDArray[np.float64], second_quaternion: npt.NDArray[np.float64]
    ) -> npt.NDArray[np.float64]:
        """
        Calculates the quaternion multiplication. quaternion multiplication is not commutative, e.g. q1q2 =/= q2q1
        :param first_quaternion: numpy array with the first quaternion in row form
        :param second_quaternion: numpy array with the second quaternion in row form
        :return: numpy array with the multiplied quaternion
        """
        w1, x1, y1, z1 = first_quaternion
        w2, x2, y2, z2 = second_quaternion

        w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
        z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2
        return np.array([w, x, y, z])

    @staticmethod
    def _calculate_quaternion_conjugate(quaternion: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        """
        Calculates the conjugate of a quaternion
        :param quaternion: numpy array with a quaternion in row form
        :return: numpy array with the quaternion conjugate
        """
        w, x, y, z = quaternion
        return np.array([w, -x, -y, -z])

    def _set_up(self) -> None:
        """
        Sets up the initial values for the data processor. This includes setting the initial
        altitude, the initial orientation of the rocket, and the initial gravity vector. This should
        only be called once, when the first data packets are passed in.
        """
        # Setting last data point as the first element, makes it so that the time diff
        # automatically becomes 0, and the velocity becomes 0
        self._last_data_packet = self._data_packets[0]

        # This is us getting the rocket's initial altitude from the mean of the first data packets
        self._initial_altitude = np.mean(
            np.array([data_packet.estPressureAlt for data_packet in self._data_packets], dtype=np.float64)
        )

        # This is us getting the rocket's initial orientation
        self._current_orientation_quaternions = np.array(
            [
                self._last_data_packet.estOrientQuaternionW,
                self._last_data_packet.estOrientQuaternionX,
                self._last_data_packet.estOrientQuaternionY,
                self._last_data_packet.estOrientQuaternionZ,
            ]
        )

        # We also get the initial gravity vector to determine which direction is up
        # Important to note that when the compensated acceleration reads -9.8 when on the
        # ground, the upwards direction of the gravity vector will be positive, not negative
        gravity_orientation = np.array(
            [
                self._last_data_packet.estGravityVectorX,
                self._last_data_packet.estGravityVectorY,
                self._last_data_packet.estGravityVectorZ,
            ]
        )

        # Gets the index for the direction (x, y, or z) that is pointing upwards
        self._gravity_upwards_index = np.argmax(np.abs(gravity_orientation))

        # on the physical IMU there is a depiction of the orientation. If a negative direction is
        # pointing to the sky, by convention, we define the gravity direction as negative. Otherwise, if
        # a positive direction is pointing to the sky, we define the gravity direction as positive.
        # For purposes of standardizing the sign of accelerations that come out of calculate_rotated_accelerations,
        # we define acceleration from motor burn as positive, acceleration due to drag as negative, and
        # acceleration on the ground to be +9.8.
        self._gravity_direction = 1 if gravity_orientation[self._gravity_upwards_index] < 0 else -1

    def _calculate_current_altitudes(self) -> npt.NDArray[np.float64]:
        """
        Calculates the current altitudes, by zeroing out the initial altitude.
        :return: A numpy array of the current altitudes of the rocket at each data point
        """
        # Get the pressure altitudes from the data points
        altitudes = np.array([data_packet.estPressureAlt for data_packet in self._data_packets], dtype=np.float64)
        # Zero out the initial altitude
        return altitudes - self._initial_altitude

    def _calculate_rotated_accelerations(self) -> list[npt.NDArray[np.float64]]:
        """
        Calculates the rotated acceleration vector. Converts gyroscope data into a delta quaternion, and adds
        onto the last quaternion. Will most likely be replaced by IMU quaternion data in the future, this
        is a work-around due to bad datasets.

        :return: numpy list of rotated acceleration vector [x,y,z]
        """

        # We pre-allocate the space for our accelerations first
        len_data_packets = len(self._data_packets)
        rotated_accelerations = [
            np.zeros(len_data_packets),
            np.zeros(len_data_packets),
            np.zeros(len_data_packets),
        ]

        # Iterates through the data points and time differences between the data points
        for idx, (data_packet, dt) in enumerate(zip(self._data_packets, self._time_differences, strict=True)):
            # Accelerations are in m/s^2
            x_accel = data_packet.estCompensatedAccelX
            y_accel = data_packet.estCompensatedAccelY
            z_accel = data_packet.estCompensatedAccelZ
            # Angular rates are in rads/s
            gyro_x = data_packet.estAngularRateX
            gyro_y = data_packet.estAngularRateY
            gyro_z = data_packet.estAngularRateZ

            # If we are missing the data points, then say accelerations are zero
            if any(val is None for val in [x_accel, y_accel, z_accel, gyro_x, gyro_y, gyro_z]):
                return rotated_accelerations

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

            delta_quat = 0.5 * np.matmul(gyro_to_quaternion_matrix, np.transpose(self._current_orientation_quaternions))
            # Updates quaternion by adding delta quaternion, and rotates acceleration vector
            self._current_orientation_quaternions += np.transpose(delta_quat) * dt
            # Normalize quaternion
            self._current_orientation_quaternions /= np.linalg.norm(self._current_orientation_quaternions)
            # Rotate acceleration by quaternion
            accel_quat = np.array([0, x_accel, y_accel, z_accel])
            accel_rotated_quat = self._multiply_quaternions(
                self._multiply_quaternions(self._current_orientation_quaternions, accel_quat),
                self._calculate_quaternion_conjugate(self._current_orientation_quaternions),
            )
            # multiplies by gravity direction, so direction of acceleration will be the same sign regarless
            # of IMU orientation.
            accel_rotated_quat *= self._gravity_direction

            # Adds the accelerations to our list of rotated accelerations
            rotated_accelerations[0][idx] = accel_rotated_quat[1]
            rotated_accelerations[1][idx] = accel_rotated_quat[2]
            rotated_accelerations[2][idx] = accel_rotated_quat[3]

        return rotated_accelerations

    def _calculate_vertical_velocity(self) -> npt.NDArray[np.float64]:
        """
        Calculates the velocity of the rocket based on the linear acceleration. Integrates the
        linear acceleration to get the velocity.
        :return: A numpy array of the velocity of the rocket at each data point
        """
        # Gets the vertical accelerations from the rotated acceleration vectors. gravity needs to be
        # subtracted from vertical acceleration, Then deadbanded.
        vertical_accelerations = np.array(
            [
                deadband(vertical_acceleration - GRAVITY, ACCELERATION_NOISE_THRESHOLD)
                for vertical_acceleration in self._rotated_accelerations[self._gravity_upwards_index]
            ]
        )

        # Integrate the accelerations to get the velocities
        vertical_velocities = self._previous_vertical_velocity + np.cumsum(
            vertical_accelerations * self._time_differences
        )

        # Store the last calculated velocity vectors
        self._previous_vertical_velocity = vertical_velocities[-1]

        return vertical_velocities

    def _calculate_time_differences(self) -> npt.NDArray[np.float64]:
        """
        Calculates the time difference between each data point and the previous data point. This cannot
        be called on the first update as _last_data_packet is None.
        :return: A numpy array of the time difference between each data point and the previous data point.
        """
        # calculate the time differences between each data point
        # We are converting from ns to s, since we don't want to have a velocity in m/ns^2
        # We are using the last data point to calculate the time difference  between the last data point from the
        # previous loop, and the first data point from the current loop
        return np.diff([data_packet.timestamp for data_packet in [self._last_data_packet, *self._data_packets]]) * 1e-9
