"""Module for processing IMU data on a higher level."""

import statistics as stats
from collections.abc import Sequence

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket


class IMUDataProcessor:
    """
    Performs high level calculations on the data packets received from the IMU. Includes
    calculation the rolling averages of acceleration, maximum altitude so far, etc., from the set of
    data points.

    :param data_points: A sequence of EstimatedDataPacket objects to process.
    """

    __slots__ = ("_avg_accel", "_avg_accel_mag", "_data_points", "_max_altitude")

    def __init__(self, data_points: Sequence[EstimatedDataPacket]):
        self._avg_accel: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._avg_accel_mag: float = 0.0
        self._max_altitude: float = 0.0
        self._data_points: Sequence[EstimatedDataPacket]

        if data_points:  # actually update the data on init
            self.update_data(data_points)
        else:
            self._data_points: Sequence[EstimatedDataPacket] = data_points

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"avg_acceleration={self.avg_acceleration}, "
            f"avg_acceleration_mag={self.avg_acceleration_mag}, "
            f"max_altitude={self.max_altitude})"
        )

    def update_data(self, data_points: Sequence[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process. This will recalculate the averages and maximum
        altitude.
        :param data_points: A sequence of EstimatedDataPacket objects to process.
        """
        if not data_points:  # Data packets may not be EstimatedDataPacket in the beginning
            return
        self._data_points = data_points
        a_x, a_y, a_z = self._compute_averages()
        self._avg_accel = (a_x, a_y, a_z)
        self._avg_accel_mag = (self._avg_accel[0] ** 2 + self._avg_accel[1] ** 2 + self._avg_accel[2] ** 2) ** 0.5
        self._max_altitude = max(*(data_point.estPressureAlt for data_point in self._data_points), self._max_altitude)

    def _compute_averages(self) -> tuple[float, float, float]:
        """
        Calculates the average acceleration and acceleration magnitude of the data points.
        :return: A tuple of the average acceleration in the x, y, and z directions.
        """
        # calculate the average acceleration in the x, y, and z directions
        # TODO: Test what these accel values actually look like
        x_accel = stats.fmean(data_point.estCompensatedAccelX for data_point in self._data_points)
        y_accel = stats.fmean(data_point.estCompensatedAccelY for data_point in self._data_points)
        z_accel = stats.fmean(data_point.estCompensatedAccelZ for data_point in self._data_points)
        # TODO: Calculate avg velocity if that's also available
        return x_accel, y_accel, z_accel

    @property
    def avg_acceleration_z(self) -> float:
        """
        Returns the average acceleration in the z direction of the data points, in m/s^2.
        """
        return self._avg_accel[-1]

    @property
    def avg_acceleration(self) -> tuple[float, float, float]:
        """
        Returns the averaged acceleration as a vector of the data points, in m/s^2.
        """
        return self._avg_accel

    @property
    def avg_acceleration_mag(self) -> float:
        """
        Returns the magnitude of the acceleration vector of the data points, in m/s^2.
        """
        return self._avg_accel_mag

    @property
    def max_altitude(self) -> float:
        """
        Returns the highest altitude attained by the rocket for the entire flight so far, in meters.
        """
        return self._max_altitude
