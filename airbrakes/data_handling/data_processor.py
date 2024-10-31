"""Module for processing IMU data on a higher level."""

from collections import deque

import numpy as np
import numpy.typing as npt
from scipy.spatial.transform import Rotation as R

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
        self._current_orientation_quaternions: R | None = None
        self._rotated_accelerations: npt.NDArray[np.float64] = np.array([0.0])
        self._data_packets: list[EstimatedDataPacket] = []
        self._time_differences: npt.NDArray[np.float64] = np.array([0.0])

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
                self._rotated_accelerations,
                self._time_differences,
                strict=True,
            )
        )

    def _first_update(self) -> None:
        """
        Sets up the initial values for the data processor. This includes setting the initial
        altitude, and the initial orientation of the rocket. This should
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
        # Convert initial orientation quaternion array to a scipy Rotation object
        # This will automatically normalize the quaternion as well:
        self._current_orientation_quaternions = R.from_quat(
            np.array(
                [
                    self._last_data_packet.estOrientQuaternionW,
                    self._last_data_packet.estOrientQuaternionX,
                    self._last_data_packet.estOrientQuaternionY,
                    self._last_data_packet.estOrientQuaternionZ,
                ]
            ),
            scalar_first=True,  # This means the order is w, x, y, z.
        )

    def _calculate_current_altitudes(self) -> npt.NDArray[np.float64]:
        """
        Calculates the current altitudes, by zeroing out the initial altitude.
        :return: A numpy array of the current altitudes of the rocket at each data point
        """
        # Get the pressure altitudes from the data points
        altitudes = np.array([data_packet.estPressureAlt for data_packet in self._data_packets], dtype=np.float64)
        # Zero out the initial altitude
        return altitudes - self._initial_altitude

    def _calculate_rotated_accelerations(self) -> npt.NDArray[np.float64]:
        """
        Calculates the rotated acceleration vector. Converts gyroscope data into a delta quaternion, and adds
        onto the last quaternion. Will most likely be replaced by IMU quaternion data in the future, this
        is a work-around due to bad datasets.

        :return: numpy list of rotated acceleration vector [x,y,z]
        """

        # We pre-allocate the space for our accelerations first
        rotated_accelerations = np.zeros(len(self._data_packets))

        current_orientation = self._current_orientation_quaternions
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

            # Check for missing data points
            if any(val is None for val in [x_accel, y_accel, z_accel, gyro_x, gyro_y, gyro_z]):
                return rotated_accelerations

            # scipy docs for more info: https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.html
            # Calculate the delta quaternion from the angular rates
            delta_rotation = R.from_rotvec([gyro_x * dt, gyro_y * dt, gyro_z * dt])

            # Update the current orientation by applying the delta rotation
            current_orientation = current_orientation * delta_rotation

            # Rotate the acceleration vector using the updated orientation
            rotated_accel = current_orientation.apply([x_accel, y_accel, z_accel])
            # Vertical acceleration will always be the 4th element of the quaternion, regardless of orientation.
            # For simplicity, we multiply by -1 so that acceleration during motor burn is positive, and
            # acceleration due to drag force during coast phase is negative.
            rotated_accelerations[idx] = -rotated_accel[2]

        # Update the class attribute with the latest quaternion orientation
        self._current_orientation_quaternions = current_orientation

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
                for vertical_acceleration in self._rotated_accelerations
            ]
        )
        # Technical notes: Trying to vectorize the deadband function via np.vectorize() or np.frompyfunc() is
        # slower than this approach.

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
        be called on the first update as _last_data_packet is None. Units are in seconds.
        :return: A numpy array of the time difference between each data point and the previous data point.
        """
        # calculate the time differences between each data point
        # We are converting from ns to s, since we don't want to have a velocity in m/ns^2
        # We are using the last data point to calculate the time difference  between the last data point from the
        # previous loop, and the first data point from the current loop
        return np.diff([data_packet.timestamp * 1e-9 for data_packet in [self._last_data_packet, *self._data_packets]])
