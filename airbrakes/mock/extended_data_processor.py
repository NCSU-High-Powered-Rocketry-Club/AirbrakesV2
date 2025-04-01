"""Module for the ExtendedDataProcessor class."""

import numpy as np
import numpy.typing as npt

from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket


class ExtendedDataProcessor(DataProcessor):
    """This class processes extra information in addition to the regular data processor. This
    data is only used in the mock replay and sims, and not in the real flight."""

    __slots__ = (
        "_average_vertical_acceleration",
        "_current_pressure_altitudes",
        "_horizontal_distances",
        "_horizontal_velocities",
        "_max_pressure_altitude",
        "_max_total_velocity",
        "_max_vertical_acceleration",
        "_total_velocity",
    )

    def __init__(self) -> None:
        super().__init__()
        # Initialize (2, 1) array for horizontal velocities:
        self._horizontal_velocities: npt.NDArray[np.float64] = np.zeros((2, 1))
        self._horizontal_distances: npt.NDArray[np.float64] = np.zeros((2, 1))
        self._current_pressure_altitudes: npt.NDArray[np.float64] = np.array([0.0])
        self._max_pressure_altitude: np.float64 = np.float64(0.0)
        self._total_velocity: np.float64 = np.float64(0.0)
        self._max_total_velocity: np.float64 = np.float64(0.0)
        self._average_vertical_acceleration: np.float64 = np.float64(0.0)
        self._max_vertical_acceleration: np.float64 = np.float64(0.0)

    @property
    def x_distance(self) -> float:
        """The horizontal distance the rocket has traveled in the x direction"""
        return float(self._horizontal_distances[0, -1])

    @property
    def y_distance(self) -> float:
        """The horizontal distance the rocket has traveled in the y direction"""
        return float(self._horizontal_distances[1, -1])

    @property
    def total_velocity(self) -> float:
        """The total velocity of the rocket, i.e the magnitude of the horizontal and vertical
        velocities."""
        return float(self._total_velocity)

    @property
    def max_total_velocity(self) -> float:
        """The maximum total velocity of the rocket."""
        return float(self._max_total_velocity)

    @property
    def average_vertical_acceleration(self) -> float:
        """The average vertical acceleration of the rocket."""
        return float(self._average_vertical_acceleration)

    @property
    def max_vertical_acceleration(self) -> float:
        """The maximum vertical acceleration of the rocket."""
        return float(self._max_vertical_acceleration)

    @property
    def current_pressure_altitude(self) -> float:
        """
        The current pressure altitude of the rocket based on the last estimated data packet.
        :return: The current pressure altitude of the rocket
        """
        return float(self._current_pressure_altitudes[-1])

    @property
    def max_pressure_altitude(self) -> float:
        """
        The maximum pressure altitude of the rocket based on the last estimated data packet.
        :return: The maximum pressure altitude of the rocket
        """
        return float(self._max_pressure_altitude)

    @property
    def horizontal_range(self) -> float:
        """
        The horizontal range of the rocket based on the horizontal distance.
        :return: The horizontal range of the rocket at the last data packet
        """
        return float(np.linalg.norm(self._horizontal_distances[:, -1]))

    def update(self, data_packets: list[EstimatedDataPacket]) -> None:
        super().update(data_packets)
        self._horizontal_velocities = self._calculate_horizontal_velocity()
        self._horizontal_distances = self._calculate_horizontal_distance()
        self._current_pressure_altitudes = self._calculate_pressure_altitudes()
        self._max_pressure_altitude = max(
            self._current_pressure_altitudes.max(), self._max_pressure_altitude
        )

        # Join the _vertical_velocity and _horizontal_velocity arrays:
        self._total_velocity = self._calculate_total_velocity()
        self._max_total_velocity = max(self._total_velocity, self._max_total_velocity)

        # Calculate the maximum vertical acceleration
        self._average_vertical_acceleration = self._calculate_average_vertical_acceleration()
        self._max_vertical_acceleration = max(
            self._max_vertical_acceleration, self._average_vertical_acceleration
        )

    def _calculate_pressure_altitudes(self) -> npt.NDArray[np.float64]:
        """Purely only calculates the pressure altitude, by zeroing the initial altitude.
        This is used to compare the difference from current_altitude when airbrakes are deployed.
        :return: A numpy array of the current altitudes of the rocket at each data point
        """
        return np.array(
            [
                data_packet.estPressureAlt - self._initial_altitude
                for data_packet in self._data_packets
            ],
        )

    def _calculate_total_velocity(self) -> np.float64:
        """Calculates the total velocity of the rocket based on the horizontal and vertical
        velocities."""
        return np.linalg.norm(
            np.hstack((self._horizontal_velocities[:, -1], self._vertical_velocities[-1]))
        )

    def _calculate_horizontal_velocity(self) -> npt.NDArray[np.float64]:
        """
        Calculates the velocity of the rocket based on the rotated acceleration. Integrates that
        acceleration to get the velocity.
        :return: A numpy array of the horizontal velocity of the rocket at each data packet
        """
        # Initialize horizontal velocities array with the previous value
        horizontal_velocities = np.zeros((2, len(self._data_packets)))

        # Integrate the accelerations to get the velocities
        for i in range(2):  # For both x and y components
            horizontal_velocities[i] = self._horizontal_velocities[i, -1] + np.cumsum(
                self._rotated_accelerations[i] * self._time_differences
            )

        return horizontal_velocities

    def _calculate_horizontal_distance(self) -> npt.NDArray[np.float64]:
        """
        Calculates the distance of the rocket based on the horizontal velocity. Integrates that
        velocity to get the distance.
        :return: A numpy array of the horizontal distance of the rocket at each data packet
        """
        horizontal_distances = np.zeros((2, len(self._data_packets)))

        # Integrate the velocities to get the distances
        for i in range(2):
            horizontal_distances[i] = self._horizontal_distances[i, -1] + np.cumsum(
                self._horizontal_velocities[i] * self._time_differences
            )

        return horizontal_distances
