"""Module for processing FIRM data on a higher level."""

from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt

from airbrakes.constants import GRAVITY_METERS_PER_SECOND_SQUARED
from airbrakes.data_handling.packets.processor_data_packet import (
    ProcessorDataPacket,
)

if TYPE_CHECKING:
    from firm_client import FIRMDataPacket


class DataProcessor:
    """
    Performs high-level calculations on the data packets received from FIRM.

    Includes calculation the vertical acceleration, velocity, maximum
    altitude so far, etc., from the set of data points.
    """

    __slots__ = (
        "_current_altitudes",
        "_data_packets",
        "_initial_altitude",
        "_integrating_for_altitude",
        "_last_data_packet",
        "_max_altitude",
        "_max_vertical_velocity",
        "_previous_altitude",
        "_previous_vertical_velocity",
        "_rotated_raw_accelerations",
        "_time_differences",
        "_vertical_accelerations",
        "_vertical_velocities",
        "_vertical_velocities_raw_accel",
    )

    def __init__(self):
        """
        Initializes the DataProcessor object.

        It processes data points to calculate various things we need
        such as the maximum altitude, vertical acceleration, velocity,
        etc. All numbers in this class are handled with numpy. This
        class also has properties to return some of these values.
        """
        self._vertical_accelerations: npt.NDArray[np.float64] = np.array([0.0])
        self._vertical_velocities: npt.NDArray[np.float64] = np.array([0.0])
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0])
        self._rotated_raw_accelerations: npt.NDArray[np.float64] = np.array([0.0])
        self._max_altitude: np.float64 = np.float64(0.0)
        self._max_vertical_velocity: np.float64 = np.float64(0.0)
        self._last_data_packet: FIRMDataPacket | None = None
        self._data_packets: list[FIRMDataPacket] = []
        self._integrating_for_altitude = False
        self._time_differences: npt.NDArray[np.float64] = np.array([0.0])
        self._previous_altitude: np.float64 = np.float64(0.0)
        self._initial_altitude: float | None= None

    @property
    def max_altitude(self) -> float:
        """
        Returns the highest altitude (zeroed-out) attained by the rocket for
        the entire flight so far, in meters.

        :return: the maximum zeroed-out altitude of the rocket.
        """
        return float(self._max_altitude)

    @property
    def current_altitude(self) -> float:
        """
        Returns the altitudes of the rocket (zeroed out) from the data
        points, in meters.

        :return: the current zeroed-out altitude of the rocket.
        """
        return float(self._current_altitudes[-1])

    @property
    def vertical_velocity(self) -> float:
        """
        The current vertical velocity of the rocket in m/s.

        Calculated by integrating the compensated acceleration after
        rotating it to the vertical direction.
        :return: The vertical velocity of the rocket.
        """
        return float(self._vertical_velocities[-1])

    @property
    def max_vertical_velocity(self) -> float:
        """
        The maximum vertical velocity the rocket has attained during the
        flight, in m/s.

        :return: The maximum vertical velocity of the rocket.
        """
        return float(self._max_vertical_velocity)

    @property
    def average_vertical_acceleration(self) -> float:
        """
        The average vertical acceleration of the rocket in m/s^2.

        :return: The average vertical acceleration of the rocket.
        """
        return float(np.mean(self._vertical_accelerations))

    @property
    def current_timestamp_seconds(self) -> float:
        """
        The timestamp of the last data packet in seconds.

        :return: the current timestamp of the most recent
            FIRMDataPacket.
        """
        try:
            return self._last_data_packet.timestamp_seconds
        except AttributeError:  # If we don't have a last data packet
            return 0

    def update(self, data_packets: list[FIRMDataPacket]) -> None:
        """
        Updates the data points to process.

        This will recompute all information such as altitude, velocity,
        etc.
        :param data_packets: A list of FIRMDataPacket objects to process
        """
        # If the data points are empty, we don't want to try to process anything
        if not data_packets:
            return

        self._data_packets = data_packets

        # If this is the first update, we can' t calculate anything yet
        if self._last_data_packet is None:
            self._last_data_packet = self._data_packets[-1]
            self._initial_altitude = float(np.mean(
                [data_packet.est_position_z_meters for data_packet in self._data_packets],
            ))
            self._vertical_accelerations[0] = (
                self._last_data_packet.est_acceleration_z_gs * GRAVITY_METERS_PER_SECOND_SQUARED
            )
            self._vertical_velocities[0] = self._last_data_packet.est_velocity_z_meters_per_s
            self._current_altitudes[0] = self._last_data_packet.est_position_z_meters
            self._max_altitude = np.float64(self._last_data_packet.est_position_z_meters)
            self._max_vertical_velocity = max(self._vertical_velocities)
            return

        self._time_differences = self._calculate_time_differences()
        self._vertical_accelerations = GRAVITY_METERS_PER_SECOND_SQUARED * np.fromiter(
            (packet.est_acceleration_z_gs for packet in self._data_packets), dtype=np.float64
        )
        self._vertical_velocities = np.fromiter(
            (packet.est_velocity_z_meters_per_s for packet in self._data_packets), dtype=np.float64)

        self._current_altitudes = self._calculate_current_altitudes()

        self._max_vertical_velocity = max(
            self._vertical_velocities.max(), self._max_vertical_velocity
        )

        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        # Store the last data point for the next update
        self._last_data_packet = data_packets[-1]

    def prepare_for_extending_airbrakes(self) -> None:
        """
        When we extend the airbrakes, it messes with the pressure sensor which messes up the
        altitude data.

        Additionally, the velocity data could have accumulated error due to the strong acceleration
        from the motor burn. Because of these things, this function makes the data processor start
        integrating for altitude.
        """
        self._integrating_for_altitude = True

    def prepare_for_retracting_airbrakes(self) -> None:
        """
        After we retract airbrakes, we want to switch back to using pressure altitude, but we need
        to wait a little bit of time for the pressure to stabilize.
        """
        self._integrating_for_altitude = False

    def _calculate_current_altitudes(self) -> npt.NDArray[np.float64]:
        """
        Calculates the current altitudes, by zeroing out the initial altitude.

        It either uses the altitude from the pressure sensor, or integrates acceleration for the
        altitude.
        :return: A numpy array of the current altitudes of the rocket at each data point
        """
        # While the airbrakes are extended, we integrate acceleration for the altitude rather than
        # using the pressure sensor data. This is because the pressure sensor data is unreliable
        # when the airbrakes are extended as the pressure gets fucky
        if self._integrating_for_altitude:
            # Integrate the vertical velocities to get altitudes:
            # Start with the previous altitude and add the cumulative sum of (velocity * dt).
            altitudes = self._previous_altitude + np.cumsum(
                self._vertical_velocities * self._time_differences
            )
        else:
            altitudes = np.array(
                [
                    data_packet.est_position_z_meters - self._initial_altitude
                    for data_packet in self._data_packets
                ],
            )

            # Update the stored previous altitude for the next calculation.
        self._previous_altitude = altitudes[-1]

        # Get the pressure altitudes from the data points and zero out the initial altitude
        return altitudes

    def _calculate_time_differences(self) -> npt.NDArray[np.float64]:
        """
        Calculates the time difference between each data packet and the previous data packet.

        This cannot be called on the first update as _last_data_packet is None. Units are in
        seconds.
        :return: A numpy array of the time difference between each data packet and the previous data
            packet.
        """
        # calculate the time differences between each data packet
        # We are converting from ns to s, since we don't want to have a velocity in m/ns^2
        # We are using the last data packet to calculate the time difference between the last data
        # packet from the previous loop, and the first data packet from the current loop

        timestamps_in_seconds = np.array(
            [
                data_packet.timestamp_seconds
                for data_packet in [self._last_data_packet, *self._data_packets]
            ]
        )
        # Not using np.diff() results in a ~40% speedup!
        return timestamps_in_seconds[1:] - timestamps_in_seconds[:-1]

    def get_processor_data_packets(self) -> list[ProcessorDataPacket]:
        """
        Processes the data points and returns a list of ProcessorDataPackets. These will correspond
        one-to-one with the estimated data packets most recently passed in by update().

        The length of the list should be the same as the length of the list of estimated data
        packets most recently passed in by update()
        :return: A list of ProcessorDataPacket objects.
        """
        return [
            ProcessorDataPacket(
                current_altitude=float(self._current_altitudes[i]),
                vertical_velocity = float(self._vertical_velocities[i])
            )
            for i in range(len(self._data_packets))
        ]