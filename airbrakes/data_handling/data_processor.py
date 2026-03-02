"""Module for processing FIRM data on a higher level."""

from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import quaternion

from airbrakes.constants import GRAVITY_METERS_PER_SECOND_SQUARED

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
        "_last_data_packet",
        "_longitudinal_axis",
        "_max_altitude",
        "_max_vertical_velocity",
        "_vertical_accelerations",
        "_vertical_velocities",
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
        self._max_altitude: np.float64 = np.float64(0.0)
        self._max_vertical_velocity: np.float64 = np.float64(0.0)
        self._last_data_packet: FIRMDataPacket = None
        self._data_packets: list[FIRMDataPacket] = []
        # The axis the IMU is on:
        self._longitudinal_axis: quaternion.quaternion = quaternion.quaternion(0, 0, 0, 0)

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
    def average_pitch(self) -> float:
        """
        The average pitch of the rocket in degrees.

        0 degrees is nose up, 90 degrees is horizontal, and 180 degrees is nose down.
        """
        current_orientation_quat = quaternion.from_float_array(
            [
                self._last_data_packet.est_quaternion_w,
                self._last_data_packet.est_quaternion_x,
                self._last_data_packet.est_quaternion_y,
                self._last_data_packet.est_quaternion_z,
            ],
        )
        if self._last_data_packet is not None:
            rotated = (
                current_orientation_quat
                * self._longitudinal_axis
                * current_orientation_quat.conjugate()
            )
            current_orientation = rotated.vec
            dot_product = np.clip(np.dot(current_orientation, [0, 0, 1]), -1.0, 1.0)
            return np.degrees(np.arccos(dot_product))
        return 0.0

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

        # If this is the first update, we can't calculate anything yet
        if self._last_data_packet is None:
            self._first_update()
            return

        self._vertical_accelerations = GRAVITY_METERS_PER_SECOND_SQUARED * np.fromiter(
            (packet.est_acceleration_z_gs for packet in self._data_packets), dtype=np.float64
        )
        self._vertical_velocities = np.fromiter(
            (packet.est_velocity_z_meters_per_s for packet in self._data_packets), dtype=np.float64
        )
        self._current_altitudes = np.fromiter(
            (packet.est_position_z_meters for packet in self._data_packets), dtype=np.float64
        )

        self._max_vertical_velocity = max(
            self._vertical_velocities.max(), self._max_vertical_velocity
        )

        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        # Store the last data point for the next update
        self._last_data_packet = data_packets[-1]

    def _first_update(self) -> None:
        """
        Sets up the initial values for the data processor.

        This includes setting the initial altitude, and the initial orientation of the rocket. This
        should only be called once, when the first estimated data packets are passed in.
        """
        self._last_data_packet = self._data_packets[-1]
        self._vertical_accelerations[0] = (
            self._last_data_packet.est_acceleration_z_gs * GRAVITY_METERS_PER_SECOND_SQUARED
        )
        self._vertical_velocities[0] = self._last_data_packet.est_velocity_z_meters_per_s
        self._current_altitudes[0] = self._last_data_packet.est_position_z_meters
        self._max_altitude = np.float64(self._last_data_packet.est_position_z_meters)
        self._max_vertical_velocity = np.float64(self._last_data_packet.est_velocity_z_meters_per_s)

        # Get the longitudinal axis the IMU is on:
        current_orientation_quat = quaternion.from_float_array(
            [
                self._last_data_packet.est_quaternion_w,
                self._last_data_packet.est_quaternion_x,
                self._last_data_packet.est_quaternion_y,
                self._last_data_packet.est_quaternion_z,
            ]
        )

        # Since we don't have a gravity vector, we use quaternions from FIRM, which are in the
        # global frame:
        # Credit to Gemini 3.1 Pro for the following code:
        candidate_axes = [
            np.array([1.0, 0.0, 0.0]),
            np.array([-1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([0.0, -1.0, 0.0]),
            np.array([0.0, 0.0, 1.0]),
            np.array([0.0, 0.0, -1.0]),
        ]

        best_axis: npt.NDArray[np.float64] = np.array([0.0, 0.0, 0.0])
        max_z = -float("inf")

        for axis in candidate_axes:
            # Convert candidate to quaternion for rotation
            axis_quat = quaternion.from_float_array([0.0, axis[0], axis[1], axis[2]])
            # Rotate candidate to world frame
            rotated = current_orientation_quat * axis_quat * current_orientation_quat.conjugate()

            # We want the axis most aligned with the sky (Positive Z)
            if rotated.z > max_z:
                max_z = rotated.z
                best_axis = axis

        # Set the true longitudinal axis dynamically
        self._longitudinal_axis = quaternion.from_float_array(
            [0.0, best_axis[0], best_axis[1], best_axis[2]]
        )
