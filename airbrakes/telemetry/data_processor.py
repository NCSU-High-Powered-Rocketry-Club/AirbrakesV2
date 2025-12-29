"""
Module for processing IMU data on a higher level.
"""

from collections import deque
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import quaternion

from airbrakes.constants import (
    ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
    GRAVITY_METERS_PER_SECOND_SQUARED,
    SECONDS_UNTIL_PRESSURE_STABILIZATION,
    WINDOW_SIZE_FOR_PRESSURE_ZEROING,
)
from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.utils import convert_ns_to_s

if TYPE_CHECKING:
    from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket


class DataProcessor:
    """
    Performs high level calculations on the estimated data packets received from the IMU.

    Includes calculation the vertical acceleration, velocity, maximum altitude so far, etc., from
    the set of data points.
    """

    __slots__ = (
        "_current_altitudes",
        "_current_orientation_quaternions",
        "_data_packets",
        "_initial_altitude",
        "_integrating_for_altitude",
        "_last_data_packet",
        "_longitudinal_axis",
        "_max_altitude",
        "_max_vertical_velocity",
        "_pressure_alt_buffer",
        "_previous_altitude",
        "_previous_vertical_velocity",
        "_retraction_timestamp",
        "_rotated_accelerations",
        "_time_differences",
        "_vertical_velocities",
    )

    def __init__(self):
        """
        Initializes the IMUDataProcessor object.

        It processes data points to calculate various things we need such as the maximum altitude,
        vertical acceleration, velocity, etc. All numbers in this class are handled with numpy. This
        class also has properties to return some of these values.
        """
        self._max_altitude: np.float64 = np.float64(0.0)
        self._previous_altitude: np.float64 = np.float64(0.0)
        self._vertical_velocities: npt.NDArray[np.float64] = np.array([0.0])
        self._max_vertical_velocity: np.float64 = np.float64(0.0)
        self._previous_vertical_velocity: np.float64 = np.float64(0.0)
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0])
        self._last_data_packet: EstimatedDataPacket | None = None
        self._current_orientation_quaternions: quaternion.quaternion | None = None
        self._rotated_accelerations: npt.NDArray[np.float64] = np.zeros((1, 3), dtype=np.float64)
        self._data_packets: list[EstimatedDataPacket] = []
        self._time_differences: npt.NDArray[np.float64] = np.array([0.0])
        self._integrating_for_altitude = False
        self._retraction_timestamp: int | None = None
        # The axis the IMU is on:
        self._longitudinal_axis: quaternion.quaternion = quaternion.quaternion(0, 0, 0, 0)
        self._pressure_alt_buffer = deque(maxlen=WINDOW_SIZE_FOR_PRESSURE_ZEROING)

    @property
    def max_altitude(self) -> float:
        """
        Returns the highest altitude (zeroed-out) attained by the rocket for the entire flight so
        far, in meters.

        :return: the maximum zeroed-out altitude of the rocket.
        """
        return float(self._max_altitude)

    @property
    def current_altitude(self) -> float:
        """
        Returns the altitudes of the rocket (zeroed out) from the data points, in meters.

        :return: the current zeroed-out altitude of the rocket.
        """
        return float(self._current_altitudes[-1])

    @property
    def vertical_velocity(self) -> float:
        """
        The current vertical velocity of the rocket in m/s.

        Calculated by integrating the compensated acceleration after rotating it to the vertical
        direction.
        :return: The vertical velocity of the rocket.
        """
        return float(self._vertical_velocities[-1])

    @property
    def vertical_acceleration(self) -> float:
        """
        The current vertical acceleration of the rocket in m/s^2.

        :return: The vertical acceleration of the rocket.
        """
        return float(self._rotated_accelerations[:, 2][-1])

    @property
    def average_vertical_acceleration(self) -> float:
        """
        The average vertical acceleration of the rocket.
        """
        return self._rotated_accelerations[:, 2].mean()

    @property
    def max_vertical_velocity(self) -> float:
        """
        The maximum vertical velocity the rocket has attained during the flight, in m/s.

        :return: The maximum vertical velocity of the rocket.
        """
        return float(self._max_vertical_velocity)

    @property
    def average_pitch(self) -> float:
        """
        The average pitch of the rocket in degrees.

        0 degrees is nose up, 90 degrees is horizontal, and 180 degrees is nose down.
        """
        if self._current_orientation_quaternions is not None:
            rotated = (
                self._current_orientation_quaternions
                * self._longitudinal_axis
                * self._current_orientation_quaternions.conjugate()
            )
            current_orientation = rotated.vec
            dot_product = np.clip(np.dot(current_orientation, [0, 0, 1]), -1.0, 1.0)
            return np.degrees(np.arccos(dot_product))
        return 0.0

    @property
    def current_timestamp(self) -> int:
        """
        The timestamp of the last data packet in nanoseconds.

        :return: the current timestamp of the most recent EstimatedDataPacket.
        """
        try:
            return self._last_data_packet.timestamp
        except AttributeError:  # If we don't have a last data packet
            return 0

    def update(self, data_packets: list[EstimatedDataPacket]) -> None:
        """
        Updates the data points to process.

        This will recompute all information such as altitude, velocity, etc.
        :param data_packets: A list of EstimatedDataPacket objects to process
        """
        self._data_packets = data_packets

        # If we don't have a last data point, we can't calculate the time differences needed
        # for velocity calculation:
        if self._last_data_packet is None:
            self._first_update()

        self._time_differences = self._calculate_time_differences()

        self._rotated_accelerations = self._calculate_rotated_accelerations()
        self._vertical_velocities = self._calculate_vertical_velocity()
        self._max_vertical_velocity = max(
            self._vertical_velocities.max(), self._max_vertical_velocity
        )

        self._current_altitudes = self._calculate_current_altitudes()
        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        # Store the last data point for the next update
        self._last_data_packet = data_packets[-1]

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
                # TODO: calculate the actual velocity magnitude rather than using vertical velocity
                velocity_magnitude=float(self._vertical_velocities[i]),
                # TODO: check if this pitch is good
                current_pitch_degrees=self.average_pitch,
                vertical_velocity=float(self._vertical_velocities[i]),
                vertical_acceleration=float(self._rotated_accelerations[:, 2][i]),
                time_since_last_data_packet=float(self._time_differences[i]),
            )
            for i in range(len(self._data_packets))
        ]

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
        self._retraction_timestamp = self.current_timestamp

    def zero_out_altitude(self):
        """
        Zero out the altitude based on the average of recent altitudes.

        This is only used when the rocket is on the launch pad.
        """
        # Zero out the altitude based on the average of recent altitudes
        self._pressure_alt_buffer.extend(
            [data_packet.estPressureAlt for data_packet in self._data_packets],
        )

        # Avoid division by zero:
        if (length := len(self._pressure_alt_buffer)) > 0:
            self._initial_altitude = np.float64(sum(self._pressure_alt_buffer) / length)

    def _first_update(self) -> None:
        """
        Sets up the initial values for the data processor.

        This includes setting the initial altitude, and the initial orientation of the rocket. This
        should only be called once, when the first estimated data packets are passed in.
        """
        # Setting last data point as the first element, makes it so that the time diff
        # automatically becomes 0, and the velocity becomes 0
        self._last_data_packet = self._data_packets[0]

        # This is us getting the rocket's initial altitude from the mean of the first data packets
        self._initial_altitude = np.mean(
            [data_packet.estPressureAlt for data_packet in self._data_packets],
        )

        # This is us getting the rocket's initial orientation
        # Convert initial orientation quaternion array to a scipy Rotation object
        # This will automatically normalize the quaternion as well:
        self._current_orientation_quaternions = quaternion.from_float_array(
            np.array(
                [
                    self._last_data_packet.estOrientQuaternionW,
                    self._last_data_packet.estOrientQuaternionX,
                    self._last_data_packet.estOrientQuaternionY,
                    self._last_data_packet.estOrientQuaternionZ,
                ]
            ),
        )

        # Get the longitudinal axis the IMU is on:
        gravity_vector = np.array(
            [
                self._last_data_packet.estGravityVectorX,
                self._last_data_packet.estGravityVectorY,
                self._last_data_packet.estGravityVectorZ,
            ]
        )
        # Find the dominant axis (largest absolute component)
        abs_gravity = np.abs(gravity_vector)
        dominant_axis_idx = np.argmax(abs_gravity)

        # Set longitudinal axis as the unit vector where gravity is dominant
        longitudinal_axis = np.zeros(4)
        longitudinal_axis[dominant_axis_idx + 1] = np.sign(gravity_vector[dominant_axis_idx])
        self._longitudinal_axis = quaternion.from_float_array(longitudinal_axis)

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
        if self._integrating_for_altitude or (
            self._retraction_timestamp is not None
            and convert_ns_to_s(self.current_timestamp - self._retraction_timestamp)
            < SECONDS_UNTIL_PRESSURE_STABILIZATION
        ):
            # Integrate the vertical velocities to get altitudes:
            # Start with the previous altitude and add the cumulative sum of (velocity * dt).
            altitudes = self._previous_altitude + np.cumsum(
                self._vertical_velocities * self._time_differences
            )
        else:
            altitudes = np.array(
                [
                    data_packet.estPressureAlt - self._initial_altitude
                    for data_packet in self._data_packets
                ],
            )

        # Update the stored previous altitude for the next calculation.
        self._previous_altitude = altitudes[-1]

        # Get the pressure altitudes from the data points and zero out the initial altitude
        return altitudes

    def _calculate_rotated_accelerations(self) -> npt.NDArray[np.float64]:
        """
        Calculates the rotated accelerations.

        Converts gyroscope data into a delta quaternion, and adds onto the last quaternion.
        :return: numpy list of rotated accelerations.
        """
        # We integrate gyro to get position instead of using the quaternions from our packet
        # directly. The reason why is listed in
        # https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/107

        accelerations = []
        angular_displacement = np.zeros((len(self._data_packets), 3))

        # We don't use the quaterion.integrate_angular_velocity method since that is about
        # 7x slower than just doing it manually.

        # Iterate through the data packets and extract the accelerations and gyros
        # It is a little faster (about 200ns every update) to use one for loop rather than two
        # list comprehensions. This would change if it was say 1000 data packets in a single update.
        for i, data_packet in enumerate(self._data_packets):
            # Extract accelerations in m/s^2
            x_accel = data_packet.estCompensatedAccelX
            y_accel = data_packet.estCompensatedAccelY
            z_accel = data_packet.estCompensatedAccelZ

            # It's about 6x faster to just multiply the dt here rather than outside the loop
            # using numpy vectorization.
            dt = self._time_differences[i]
            x_gyro = data_packet.estAngularRateX
            y_gyro = data_packet.estAngularRateY
            z_gyro = data_packet.estAngularRateZ

            # Initializing the quaternion here directly is faster than using
            # quaternion.from_float_array
            accelerations.append(quaternion.quaternion(0, x_accel, y_accel, z_accel))
            angular_displacement[i, :] = [
                x_gyro * dt,
                y_gyro * dt,
                z_gyro * dt,
            ]

        current_orientation_quat = self._current_orientation_quaternions

        delta_rot_quats = quaternion.from_rotation_vector(angular_displacement)
        cum_rotations = np.cumprod(delta_rot_quats)
        new_orientation_quaternion = current_orientation_quat * cum_rotations

        rotated_accel_quat = (
            new_orientation_quaternion * accelerations * new_orientation_quaternion.conjugate()
        )
        # Discard the scalar part of the quaternion
        rotated_accelerations_positive = quaternion.as_float_array(rotated_accel_quat)[..., 1:]
        rotated_accelerations = -rotated_accelerations_positive

        # Update the instance attribute with the latest quaternion orientation
        self._current_orientation_quaternions = new_orientation_quaternion[-1]

        return rotated_accelerations

    def _calculate_vertical_velocity(self) -> npt.NDArray[np.float64]:
        """
        Calculates the velocity of the rocket based on the rotated acceleration.

        Integrates that acceleration to get the velocity.
        :return: A numpy array of the vertical velocity of the rocket at each data packet
        """
        # Gets the vertical accelerations from the rotated vertical acceleration. gravity needs to
        # be subtracted from vertical acceleration, Then deadbanded.

        # Using np.where() is faster than using our deadband() function by about ~15%
        adjusted = self._rotated_accelerations[:, 2] - GRAVITY_METERS_PER_SECOND_SQUARED
        vertical_accelerations = np.where(
            np.abs(adjusted) < ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,  # Condition to check
            0,  # If the condition is true, set to 0 (deadband)
            adjusted,  # If the condition is false, keep the adjusted value
        )
        # Integrate the accelerations to get the velocities
        vertical_velocities = self._previous_vertical_velocity + np.cumsum(
            vertical_accelerations * self._time_differences
        )

        # Store the last calculated vertical velocity.
        self._previous_vertical_velocity = vertical_velocities[-1]

        return vertical_velocities

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
                convert_ns_to_s(data_packet.timestamp)
                for data_packet in [self._last_data_packet, *self._data_packets]
            ]
        )
        # Not using np.diff() results in a ~40% speedup!
        return timestamps_in_seconds[1:] - timestamps_in_seconds[:-1]
