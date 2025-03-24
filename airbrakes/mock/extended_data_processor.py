"""Module for the ExtendedDataProcessor class."""

import numpy as np
import numpy.typing as npt

from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket


class ExtendedDataProcessor(DataProcessor):
    """This class processes extra information in addition to the regular data processor. This
    data is only used in the mock replay and sims, and not in the real flight."""

    __slots__ = ("_horizontal_distances", "_horizontal_velocities")

    def __init__(self) -> None:
        super().__init__()
        # Initialize (2, 1) array for horizontal velocities:
        self._horizontal_velocities: npt.NDArray[np.float64] = np.zeros((2, 1), dtype=np.float64)
        self._horizontal_distances: npt.NDArray[np.float64] = np.zeros((2, 1), dtype=np.float64)

    @property
    def x_distance(self) -> float:
        """The horizontal distance the rocket has traveled in the x direction"""
        return float(self._horizontal_distances[0, -1])

    @property
    def y_distance(self) -> float:
        """The horizontal distance the rocket has traveled in the y direction"""
        return float(self._horizontal_distances[1, -1])

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

    def _calculate_horizontal_velocity(self) -> npt.NDArray[np.float64]:
        """
        Calculates the velocity of the rocket based on the rotated acceleration. Integrates that
        acceleration to get the velocity.
        :return: A numpy array of the horizontal velocity of the rocket at each data packet
        """
        # Initialize horizontal velocities array with the previous value
        horizontal_velocities = np.zeros((2, len(self._data_packets)), dtype=np.float64)

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
        horizontal_distances = np.zeros((2, len(self._data_packets)), dtype=np.float64)

        # Integrate the velocities to get the distances
        for i in range(2):
            horizontal_distances[i] = self._horizontal_distances[i, -1] + np.cumsum(
                self._horizontal_velocities[i] * self._time_differences
            )

        return horizontal_distances
