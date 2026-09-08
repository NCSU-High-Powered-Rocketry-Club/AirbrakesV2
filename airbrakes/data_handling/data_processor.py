"""High-level processing for estimated IMU data."""

from collections import deque
from typing import TYPE_CHECKING, Literal

import numpy as np
import numpy.typing as npt
import quaternion

from airbrakes.constants import (
    ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
    GRAVITY_METERS_PER_SECOND_SQUARED,
    SECONDS_UNTIL_PRESSURE_STABILIZATION,
    TRANSONIC_VELOCITY_METERS_PER_SECOND,
    WINDOW_SIZE_FOR_PRESSURE_ZEROING,
)
from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
from airbrakes.utils import convert_ns_to_s

if TYPE_CHECKING:
    from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket


class DataProcessor:
    """Calculates flight-state values from estimated IMU packets."""

    __slots__ = (
        "_current_altitudes",
        "_current_orientation_quaternion",
        "_data_packets",
        "_initial_altitude",
        "_integrating_for_altitude",
        "_integrating_for_altitudes",
        "_last_data_packet",
        "_longitudinal_axis",
        "_max_altitude",
        "_max_vertical_velocity",
        "_pressure_alt_buffer",
        "_previous_altitude",
        "_previous_vertical_velocity",
        "_retraction_timestamp_seconds",
        "_rotated_accelerations",
        "_time_differences",
        "_vertical_accelerations",
        "_vertical_velocities",
    )

    def __init__(self) -> None:
        self._current_altitudes: npt.NDArray[np.float64] = np.array([0.0])
        self._current_orientation_quaternion: quaternion.quaternion | None = None
        self._data_packets: list[EstimatedDataPacket] = []
        self._initial_altitude: np.float64 | None = None
        self._integrating_for_altitude = False
        self._integrating_for_altitudes: list[Literal["T", "F"]] = ["F"]
        self._last_data_packet: EstimatedDataPacket | None = None
        self._longitudinal_axis = quaternion.quaternion(0, 0, 0, 0)
        self._max_altitude = np.float64(0.0)
        self._max_vertical_velocity = np.float64(0.0)
        self._pressure_alt_buffer: deque[float] = deque(maxlen=WINDOW_SIZE_FOR_PRESSURE_ZEROING)
        self._previous_altitude = np.float64(0.0)
        self._previous_vertical_velocity = np.float64(0.0)
        self._retraction_timestamp_seconds: float | None = None
        self._rotated_accelerations: npt.NDArray[np.float64] = np.array([0.0])
        self._time_differences: npt.NDArray[np.float64] = np.array([0.0])
        self._vertical_accelerations: npt.NDArray[np.float64] = np.array([0.0])
        self._vertical_velocities: npt.NDArray[np.float64] = np.array([0.0])

    @property
    def max_altitude(self) -> float:
        """Return the highest altitude above the launch-pad baseline in meters."""
        return float(self._max_altitude)

    @property
    def current_altitude(self) -> float:
        """Return the latest altitude above the launch-pad baseline in meters."""
        return float(self._current_altitudes[-1])

    @property
    def vertical_velocity(self) -> float:
        """Return the latest integrated vertical velocity in meters per second."""
        return float(self._vertical_velocities[-1])

    @property
    def max_vertical_velocity(self) -> float:
        """Return the largest vertical velocity seen during this flight."""
        return float(self._max_vertical_velocity)

    @property
    def average_vertical_acceleration(self) -> float:
        """Return the average gravity-including vertical acceleration for the latest batch."""
        return float(np.mean(self._rotated_accelerations))

    @property
    def average_pitch(self) -> float:
        """Return the rocket tilt, where zero degrees is aligned with the upward vertical axis."""
        if self._current_orientation_quaternion is None:
            return 0.0

        rotated = (
            self._current_orientation_quaternion
            * self._longitudinal_axis
            * self._current_orientation_quaternion.conjugate()
        )
        dot_product = np.clip(np.dot(rotated.vec, [0, 0, 1]), -1.0, 1.0)
        return float(np.degrees(np.arccos(dot_product)))

    @property
    def current_timestamp_seconds(self) -> float:
        """Return the most recent estimated-packet timestamp in seconds."""
        if self._last_data_packet is None:
            return 0.0
        return convert_ns_to_s(self._last_data_packet.timestamp)

    def update(self, data_packets: list[EstimatedDataPacket]) -> None:
        """Process a chronologically ordered batch of estimated IMU packets."""
        if not data_packets:
            return

        self._data_packets = data_packets
        if self._last_data_packet is None:
            self._first_update()

        self._time_differences = self._calculate_time_differences()
        self._rotated_accelerations = self._calculate_rotated_accelerations()
        self._vertical_accelerations = (
            self._rotated_accelerations - GRAVITY_METERS_PER_SECOND_SQUARED
        )
        self._vertical_accelerations = np.where(
            np.abs(self._vertical_accelerations) < ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
            0.0,
            self._vertical_accelerations,
        )
        self._vertical_velocities = self._calculate_vertical_velocity()
        self._current_altitudes = self._calculate_current_altitudes()

        self._max_vertical_velocity = max(
            self._vertical_velocities.max(), self._max_vertical_velocity
        )
        self._max_altitude = max(self._current_altitudes.max(), self._max_altitude)
        self._last_data_packet = data_packets[-1]

    def zero_out_altitude(self) -> None:
        """Update the launch-pad pressure-altitude baseline from the rolling standby window."""
        self._pressure_alt_buffer.extend(
            self._required(packet.estPressureAlt, "estPressureAlt") for packet in self._data_packets
        )
        if self._pressure_alt_buffer:
            self._initial_altitude = np.float64(np.mean(self._pressure_alt_buffer))

    def prepare_for_extending_airbrakes(self) -> None:
        """Use integrated altitude while airbrakes disturb the pressure sensor."""
        self._integrating_for_altitude = True

    def prepare_for_retracting_airbrakes(self) -> None:
        """Resume pressure altitude after its post-retraction stabilization interval."""
        self._integrating_for_altitude = False
        self._retraction_timestamp_seconds = self.current_timestamp_seconds

    @staticmethod
    def _required(value: float | None, field_name: str) -> float:
        if value is None:
            raise ValueError(f"Estimated IMU packet is missing required field {field_name}.")
        return value

    def _first_update(self) -> None:
        """Initialize the pressure baseline and gravity-derived longitudinal axis."""
        first_packet = self._data_packets[0]
        self._last_data_packet = first_packet
        self._initial_altitude = np.float64(
            np.mean(
                [
                    self._required(packet.estPressureAlt, "estPressureAlt")
                    for packet in self._data_packets
                ]
            )
        )

        self._current_orientation_quaternion = quaternion.from_float_array(
            np.array(
                [
                    self._required(first_packet.estOrientQuaternionW, "estOrientQuaternionW"),
                    self._required(first_packet.estOrientQuaternionX, "estOrientQuaternionX"),
                    self._required(first_packet.estOrientQuaternionY, "estOrientQuaternionY"),
                    self._required(first_packet.estOrientQuaternionZ, "estOrientQuaternionZ"),
                ]
            )
        )
        gravity_vector = np.array(
            [
                self._required(first_packet.estGravityVectorX, "estGravityVectorX"),
                self._required(first_packet.estGravityVectorY, "estGravityVectorY"),
                self._required(first_packet.estGravityVectorZ, "estGravityVectorZ"),
            ]
        )
        dominant_axis = int(np.argmax(np.abs(gravity_vector)))
        longitudinal_axis = np.zeros(4)
        longitudinal_axis[dominant_axis + 1] = np.sign(gravity_vector[dominant_axis])
        self._longitudinal_axis = quaternion.from_float_array(longitudinal_axis)

    def _calculate_current_altitudes(self) -> npt.NDArray[np.float64]:
        """Calculate pressure or integrated altitude for every packet in the latest batch."""
        altitudes = np.empty(len(self._data_packets), dtype=np.float64)
        previous_altitude = self._previous_altitude
        self._integrating_for_altitudes = []

        for index, data_packet in enumerate(self._data_packets):
            timestamp_seconds = convert_ns_to_s(data_packet.timestamp)
            integrating = self._requires_integrated_altitude(
                self._vertical_velocities[index], timestamp_seconds
            )
            self._integrating_for_altitudes.append("T" if integrating else "F")

            if integrating:
                altitude = (
                    previous_altitude
                    + self._vertical_velocities[index] * self._time_differences[index]
                )
            elif self._initial_altitude is not None:
                altitude = (
                    self._required(data_packet.estPressureAlt, "estPressureAlt")
                    - self._initial_altitude
                )
            else:
                raise RuntimeError("Pressure altitude baseline was not initialized.")

            altitudes[index] = altitude
            previous_altitude = altitude

        self._previous_altitude = previous_altitude
        return altitudes

    def _requires_integrated_altitude(
        self, vertical_velocity: float, timestamp_seconds: float
    ) -> bool:
        """Return whether pressure altitude is currently unsuitable for use."""
        return (
            self._integrating_for_altitude
            or (
                self._retraction_timestamp_seconds is not None
                and timestamp_seconds - self._retraction_timestamp_seconds
                <= SECONDS_UNTIL_PRESSURE_STABILIZATION
            )
            or abs(vertical_velocity) > TRANSONIC_VELOCITY_METERS_PER_SECOND
        )

    def _calculate_rotated_accelerations(self) -> npt.NDArray[np.float64]:
        """Rotate compensated acceleration into the vertical frame using integrated gyro motion."""
        if self._current_orientation_quaternion is None:
            raise RuntimeError("IMU orientation was not initialized.")

        accelerations: list[quaternion.quaternion] = []
        angular_displacements = np.empty((len(self._data_packets), 3))
        for index, data_packet in enumerate(self._data_packets):
            accelerations.append(
                quaternion.quaternion(
                    0,
                    self._required(data_packet.estCompensatedAccelX, "estCompensatedAccelX"),
                    self._required(data_packet.estCompensatedAccelY, "estCompensatedAccelY"),
                    self._required(data_packet.estCompensatedAccelZ, "estCompensatedAccelZ"),
                )
            )
            angular_displacements[index] = [
                self._required(data_packet.estAngularRateX, "estAngularRateX")
                * self._time_differences[index],
                self._required(data_packet.estAngularRateY, "estAngularRateY")
                * self._time_differences[index],
                self._required(data_packet.estAngularRateZ, "estAngularRateZ")
                * self._time_differences[index],
            ]

        delta_rotations = quaternion.from_rotation_vector(angular_displacements)
        orientations = self._current_orientation_quaternion * np.cumprod(delta_rotations)
        rotated_accelerations = orientations * accelerations * orientations.conjugate()
        self._current_orientation_quaternion = orientations[-1]
        return -quaternion.as_float_array(rotated_accelerations)[..., 3]

    def _calculate_vertical_velocity(self) -> npt.NDArray[np.float64]:
        """Integrate deadbanded vertical acceleration over the latest packet timestamps."""
        vertical_velocities = self._previous_vertical_velocity + np.cumsum(
            self._vertical_accelerations * self._time_differences
        )
        self._previous_vertical_velocity = vertical_velocities[-1]
        return vertical_velocities

    def _calculate_time_differences(self) -> npt.NDArray[np.float64]:
        """Calculate timestamp differences, including the previous batch's final packet."""
        if self._last_data_packet is None:
            raise RuntimeError("Cannot calculate time differences before the first IMU packet.")

        timestamps = np.array(
            [
                convert_ns_to_s(packet.timestamp)
                for packet in [self._last_data_packet, *self._data_packets]
            ]
        )
        time_differences = timestamps[1:] - timestamps[:-1]
        if np.any(time_differences < 0):
            raise ValueError("Estimated IMU packet timestamps must be chronological.")
        return time_differences

    def get_processor_data_packets(self) -> list[ProcessorDataPacket]:
        """Return one current-format processed packet per estimated IMU packet."""
        return [
            ProcessorDataPacket(
                current_altitude=float(self._current_altitudes[index]),
                integrating_for_altitude=self._integrating_for_altitudes[index],
                vertical_velocity_meters_per_s=float(self._vertical_velocities[index]),
                horizontal_velocity_meters_per_s=0.0,
                tilt_angle_degrees=self.average_pitch,
                angular_rate_deg_per_s=0.0,
                timestamp_seconds=convert_ns_to_s(data_packet.timestamp),
            )
            for index, data_packet in enumerate(self._data_packets)
        ]
