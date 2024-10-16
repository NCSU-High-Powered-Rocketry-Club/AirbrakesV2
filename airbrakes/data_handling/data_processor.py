"""Module for processing IMU data on a higher level."""

from collections import deque
from collections.abc import Sequence

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from airbrakes.utils import deadband
from constants import ACCELERATION_NOISE_THRESHOLD


class IMUDataProcessor:
    """
    Performs high level calculations on the data packets received from the IMU. Includes
    calculation the rolling averages of acceleration, maximum altitude so far, etc., from the set of
    data points.
    """

    __slots__ = (
        "_current_altitudes",
        "_data_points",
        "_initial_altitude",
        "_last_data_point",
        "_max_altitude",
        "_max_speed",
        "_previous_velocity",
        "_speeds",
        "upside_down",
    )

    def __init__(self, upside_down: bool = False):
        self.upside_down = upside_down

        self._max_altitude: np.float64 = np.float64(0.0)
        self._speeds: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._max_speed: np.float64 = np.float64(0.0)
        self._previous_velocity: npt.NDArray[np.float64] = np.array([0.0, 0.0, 0.0], dtype=np.float64)
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0], dtype=np.float64)
        self._last_data_point: EstimatedDataPacket | None = None
        self._data_points: Sequence[EstimatedDataPacket] = []

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"max_altitude={self.max_altitude}, "
            f"current_altitude={self.current_altitude}, "
            f"speed={self.speed}, "
            f"max_speed={self.max_speed})"
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

    def update(self, data_points: Sequence[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. This will recompute all the averages and other
        information such as altitude, speed, etc.
        :param data_points: A sequence of EstimatedDataPacket objects to process
        """
        self._data_points = data_points

        # If the data points are empty, we don't want to try to process anything
        if not self._data_points:
            return

        # If we don't have a last data point, we can't calculate the time differences
        if self._last_data_point is None:
            # Store the first data point for the next update
            self._last_data_point = self._data_points[0]
            # Handles the case where we only have one data point
            self._data_points = self._data_points[1:]
            if not self._data_points:
                return

        # We use linearAcceleration because we don't want gravity to affect our calculations for speed
        self._speeds = self._calculate_speeds()
        self._max_speed = max(self._speeds.max(), self._max_speed)

        self._current_altitudes = self._calculate_current_altitudes()
        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        # Store the last data point for the next update
        self._last_data_point = data_points[-1]

    def get_processed_data(self) -> deque[ProcessedDataPacket]:
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
        be called on the first update as _last_data_point is None.
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
        Returns the deadbanded accelerations in the x, y, and z directions.
        :return: A tuple of numpy arrays of the deadbanded accelerations in the x, y, and z directions.
        """
        # Pre-allocate numpy arrays to store the deadbanded accelerations in the x, y, and z directions.
        # The length of each array is the number of data points.
        x_accelerations = np.zeros(len(self._data_points), dtype=np.float64)
        y_accelerations = np.zeros(len(self._data_points), dtype=np.float64)
        z_accelerations = np.zeros(len(self._data_points), dtype=np.float64)

        # Loop through each data point and apply deadbanding to the estimated accelerations
        # in the x, y, and z directions. Store the results in the corresponding arrays.
        for i, data_point in enumerate(self._data_points):
            x_accelerations[i] = deadband(data_point.estLinearAccelX, ACCELERATION_NOISE_THRESHOLD)
            y_accelerations[i] = deadband(data_point.estLinearAccelY, ACCELERATION_NOISE_THRESHOLD)
            z_accelerations[i] = deadband(data_point.estLinearAccelZ, ACCELERATION_NOISE_THRESHOLD)

        return x_accelerations, y_accelerations, z_accelerations
