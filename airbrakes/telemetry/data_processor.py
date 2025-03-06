"""Module for processing IMU data on a higher level."""

import numpy as np
import numpy.typing as npt
from scipy.spatial.transform import Rotation as R

from airbrakes.constants import (
    ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
    GRAVITY_METERS_PER_SECOND_SQUARED,
    SECONDS_UNTIL_PRESSURE_STABILIZATION,
)
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket
from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.utils import convert_ns_to_s, deadband


class DataProcessor:
    """
    Performs high level calculations on the estimated data packets received from the IMU. Includes
    calculation the vertical acceleration, velocity, maximum altitude so far, etc., from the set of
    data points.
    """

    __slots__ = (
        "_current_altitudes",
        "_current_orientation_quaternions",
        "_data_packets",
        "_initial_altitude",
        "_integrating_for_altitude",
        "_last_data_packet",
        "_max_altitude",
        "_max_vertical_velocity",
        "_previous_altitude",
        "_previous_altitude_data_points",
        "_previous_vertical_velocity",
        "_retraction_timestamp",
        "_rotated_accelerations",
        "_store_altitude_data",
        "_time_differences",
        "_vertical_velocities",
    )

    def __init__(self):
        """
        Initializes the IMUDataProcessor object. It processes data points to calculate various
        things we need such as the maximum altitude, vertical acceleration, velocity, etc. All
        numbers in this class are handled with numpy. This class also has properties to return
        some of these values.
        """
        self._max_altitude: np.float64 = np.float64(0.0)
        self._previous_altitude: np.float64 = np.float64(0.0)
        self._vertical_velocities: npt.NDArray[np.float64] = np.array([0.0])
        self._max_vertical_velocity: np.float64 = np.float64(0.0)
        self._previous_vertical_velocity: np.float64 = np.float64(0.0)
        self._initial_altitude: np.float64 | None = None
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0])
        self._last_data_packet: EstimatedDataPacket | None = None
        self._current_orientation_quaternions: R | None = None
        self._rotated_accelerations: npt.NDArray[np.float64] = np.array([0.0])
        self._data_packets: list[EstimatedDataPacket] = []
        self._time_differences: npt.NDArray[np.float64] = np.array([0.0])
        self._integrating_for_altitude = False
        # This a list of tuples with (timestamp in seconds, altitude)
        self._previous_altitude_data_points: list[tuple[float, float]] = []
        self._store_altitude_data = False
        self._retraction_timestamp: float | None = None

    @property
    def max_altitude(self) -> float:
        """
        Returns the highest altitude (zeroed-out) attained by the rocket for the entire flight
        so far, in meters.
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
        The current vertical velocity of the rocket in m/s. Calculated by integrating the
        compensated acceleration after rotating it to the vertical direction.
        :return: The vertical velocity of the rocket.
        """
        return float(self._vertical_velocities[-1])

    @property
    def max_vertical_velocity(self) -> float:
        """
        The maximum vertical velocity the rocket has attained during the flight, in m/s.
        :return: The maximum vertical velocity of the rocket.
        """
        return float(self._max_vertical_velocity)

    @property
    def average_vertical_acceleration(self) -> float:
        """
        The average vertical acceleration of the rocket in m/s^2.
        :return: The average vertical acceleration of the rocket.
        """
        return float(np.mean(self._rotated_accelerations))

    @property
    def average_pitch(self) -> float:
        """The average pitch of the rocket in degrees"""
        if self._current_orientation_quaternions is not None:
            current_orientation = self._current_orientation_quaternions.apply([0, 0, 1])
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
        self._max_vertical_velocity = max(
            self._vertical_velocities.max(), self._max_vertical_velocity
        )

        self._current_altitudes = self._calculate_current_altitudes()
        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)

        if self._store_altitude_data:
            # Stores the altitude data points for the quadratic fit
            for i, data_packet in enumerate(data_packets):
                self._previous_altitude_data_points.append(
                    (convert_ns_to_s(data_packet.timestamp), float(self._current_altitudes[i]))
                )

        # Store the last data point for the next update
        self._last_data_packet = data_packets[-1]

    def get_processor_data_packets(self) -> list[ProcessorDataPacket]:
        """
        Processes the data points and returns a list of ProcessorDataPacket objects. The length
        of the list should be the same as the length of the list of estimated data packets most
        recently passed in by update()
        :return: A list of ProcessorDataPacket objects.
        """
        return [
            ProcessorDataPacket(
                current_altitude=self._current_altitudes[i],
                vertical_velocity=self._vertical_velocities[i],
                vertical_acceleration=self._rotated_accelerations[i],
                time_since_last_data_packet=self._time_differences[i],
            )
            for i in range(len(self._data_packets))
        ]

    def start_storing_altitude_data(self) -> None:
        """
        Starts storing altitude data for the purpose of calibrating the velocity.
        """
        self._store_altitude_data = True

    def prepare_for_extending_airbrakes(self) -> None:
        """
        When we extend the airbrakes, it messes with the pressure sensor which messes up the
        altitude data. Additionally, the velocity data could have accumulated error due to the
        strong acceleration from the motor burn. Because of these things, this function makes the
        data processor start integrating for altitude and "calibrates" the velocity.
        """
        self._store_altitude_data = False
        self._integrating_for_altitude = True

        if len(self._previous_altitude_data_points) > 0:
            # First we have to only keep the data points with unique altitudes
            data = np.array(self._previous_altitude_data_points)
            # Makes numpy arrays
            timestamps = data[:, 0]
            altitudes = data[:, 1]

            # Create a boolean mask that keeps the first point and every point where the altitude
            # changes. Basically we're just keeping the points with unique altitudes.
            mask = np.concatenate(([True], altitudes[1:] != altitudes[:-1]))
            unique_timestamps = timestamps[mask]
            unique_altitudes = altitudes[mask]

            # Makes it so the first timestamp is 0 so the polyfit doesn't shit itself
            first_timestamp = unique_timestamps[0]
            shifted_timestamps = unique_timestamps - first_timestamp

            # Fit a quadratic curve using the shifted timestamps
            coeffs = np.polyfit(shifted_timestamps, unique_altitudes, 2)
            altitude_fit = np.poly1d(coeffs)
            velocity_fit = altitude_fit.deriv()

            # This resets the vertical velocity to the value of the derivative of the quadratic
            # fit at the current time. We do this because the velocity data could have accumulated
            # error due to the strong acceleration from the motor burn.
            self._previous_vertical_velocity = velocity_fit(
                convert_ns_to_s(self.current_timestamp) - first_timestamp
            )

    def prepare_for_retracting_airbrakes(self) -> None:
        """
        After we retract airbrakes, we want to switch back to using pressure altitude, but we need
        to wait a little bit of time for the pressure to stabilize.
        """
        self._integrating_for_altitude = False
        self._retraction_timestamp = self.current_timestamp

    def _first_update(self) -> None:
        """
        Sets up the initial values for the data processor. This includes setting the initial
        altitude, and the initial orientation of the rocket. This should only be called once, when
        the first estimated data packets are passed in.
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
        Calculates the current altitudes, by zeroing out the initial altitude. It either uses the
        altitude from the pressure sensor, or integrates acceleration for the altitude.
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
        Calculates the vertical rotated accelerations. Converts gyroscope data into a delta
        quaternion, and adds onto the last quaternion.
        :return: numpy list of vertical rotated accelerations.
        """
        # We pre-allocate the space for our accelerations first
        rotated_accelerations = np.zeros(len(self._data_packets))

        current_orientation = self._current_orientation_quaternions
        # Iterates through the data points and time differences between the data points
        for i in range(len(self._data_packets)):
            data_packet = self._data_packets[i]
            dt = self._time_differences[i]
            # Accelerations are in m/s^2
            x_accel = data_packet.estCompensatedAccelX
            y_accel = data_packet.estCompensatedAccelY
            z_accel = data_packet.estCompensatedAccelZ
            # Angular rates are in rads/s
            gyro_x = data_packet.estAngularRateX
            gyro_y = data_packet.estAngularRateY
            gyro_z = data_packet.estAngularRateZ

            # scipy docs for more info: https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.html
            # Calculate the delta quaternion from the angular rates
            delta_rotation = R.from_rotvec([gyro_x * dt, gyro_y * dt, gyro_z * dt])

            # Update the current orientation by applying the delta rotation
            current_orientation = current_orientation * delta_rotation

            # Rotate the acceleration vector using the updated orientation
            rotated_accel = current_orientation.apply([x_accel, y_accel, z_accel])
            # Vertical acceleration will always be the 3rd element of the rotated vector,
            # regardless of orientation. For simplicity, we multiply by -1 so that acceleration
            # during motor burn is positive, and acceleration due to drag force during coast phase
            # is negative.
            rotated_accelerations[i] = -rotated_accel[2]

        # Update the class attribute with the latest quaternion orientation
        self._current_orientation_quaternions = current_orientation

        return rotated_accelerations

    def _calculate_vertical_velocity(self) -> npt.NDArray[np.float64]:
        """
        Calculates the velocity of the rocket based on the rotated acceleration. Integrates that
        acceleration to get the velocity.
        :return: A numpy array of the vertical velocity of the rocket at each data packet
        """
        # Gets the vertical accelerations from the rotated vertical acceleration. gravity needs to
        # be subtracted from vertical acceleration, Then deadbanded.
        vertical_accelerations = np.array(
            [
                deadband(
                    vertical_acceleration - GRAVITY_METERS_PER_SECOND_SQUARED,
                    ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
                )
                for vertical_acceleration in self._rotated_accelerations
            ]
        )
        # Technical notes: Trying to vectorize the deadband function via np.vectorize() or
        # np.frompyfunc() or np.where() is slower than this approach.

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
        :return: A numpy array of the time difference between each data packet and the previous
        data packet.
        """
        # calculate the time differences between each data packet
        # We are converting from ns to s, since we don't want to have a velocity in m/ns^2
        # We are using the last data packet to calculate the time difference between the last data
        # packet from the previous loop, and the first data packet from the current loop
        return np.diff(
            [
                convert_ns_to_s(data_packet.timestamp)
                for data_packet in [self._last_data_packet, *self._data_packets]
            ]
        )
