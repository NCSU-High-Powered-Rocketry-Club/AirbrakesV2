"""
Module that creates randomly generated data to sent to the simulation IMU.
"""

import csv
from pathlib import Path

import numpy as np
import numpy.typing as npt

from airbrakes.constants import (
    ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
    GRAVITY_METERS_PER_SECOND_SQUARED,
    MAX_VELOCITY_THRESHOLD,
)
from airbrakes.simulation.rotation_manager import RotationManager
from airbrakes.simulation.sim_config import SimulationConfig
from airbrakes.simulation.sim_utils import get_random_value
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    RawDataPacket,
)
from airbrakes.utils import deadband


class DataGenerator:
    """
    Uses config settings to generate realistic flight trajectories.

    Returns raw and estimated data points for the sim IMU to combine into data packets
    """

    __slots__ = (
        "_config",
        "_eff_exhaust_velocity",
        "_est_rotation_manager",
        "_last_est_packet",
        "_last_raw_packet",
        "_last_velocities",
        "_max_vertical_velocity",
        "_raw_rotation_manager",
        "_thrust_data",
        "is_airbrakes_extended",
    )

    def __init__(self, config: SimulationConfig):
        """
        Initializes the data generator object with the provided configuration :param config: the
        configuration object for the simulation.
        """
        self._config: SimulationConfig = config

        self._last_est_packet: EstimatedDataPacket | None = None
        self._last_raw_packet: RawDataPacket | None = None
        self._last_velocities: npt.NDArray = np.array([0.0, 0.0, 0.0])
        self._max_vertical_velocity: np.float64 = np.float64(0.1)
        self._eff_exhaust_velocity: np.float64 | None = None

        # loads thrust curve
        self._thrust_data: npt.NDArray = self._load_thrust_curve()

        # initializes the rotation manager with the launch pad conditions
        raw_manager, est_manager = self._get_rotation_managers()
        self._raw_rotation_manager: RotationManager = raw_manager
        self._est_rotation_manager: RotationManager = est_manager

        self.is_airbrakes_extended = False

    @property
    def velocity_vector(self) -> npt.NDArray:
        """
        Returns the last calculated velocity vectors of the rocket.
        """
        return self._last_velocities

    def _load_thrust_curve(self) -> npt.NDArray:
        """
        Loads the thrust curve from the motor specified in the configs.

        :return: numpy array containing lists with the time, and thrust at that time.
        """
        # gets the path of the csv based on the config file
        csv_path = Path(f"airbrakes/simulation/thrust_curves/{self._config.motor}.csv")

        # initializes the list for timestamps and thrust values
        motor_timestamps = [0]
        motor_thrusts = [0]

        start_flag = False  # flag to identify when the metadata/header rows are skipped

        with csv_path.open(mode="r", newline="") as thrust_csv:
            propellant_mass = None
            reader = csv.reader(thrust_csv)

            for row in reader:
                # We want to store the propellant mass
                if row[0] == "propellant mass:":
                    propellant_mass = float(row[1]) / 1000  # we want in kg
                    continue

                # Start appending data only after the header row
                if row == ["Time (s)", "Thrust (N)"]:
                    start_flag = True
                    continue  # Skip header row itself

                if start_flag:
                    # Convert time and thrust values to floats and append to list
                    time = float(row[0])
                    thrust = float(row[1])
                    motor_timestamps.append(time)
                    motor_thrusts.append(thrust)

            # for future mass calculations, finding total impulse
            total_impulse = np.trapezoid(motor_thrusts, motor_timestamps)
            # calculating effective exhaust velocity (constant)
            self._eff_exhaust_velocity = total_impulse / propellant_mass

        return np.array([motor_timestamps, motor_thrusts])

    def _get_rotation_managers(self) -> npt.NDArray:
        """
        Creates and initializes both rotation managers that will be used to contain any rotation
        related math, and methods for the raw and estimated data.

        :return: a 2 element array containing the raw rotation manager and the estimated rotation
            manager, respectively.
        """
        launch_rod_pitch = self._config.launch_rod_pitch
        launch_rod_azimuth = self._config.launch_rod_azimuth
        raw_manager = RotationManager(
            self._config.wgs_vertical,
            launch_rod_pitch,
            launch_rod_azimuth,
        )
        est_manager = RotationManager(
            self._config.wgs_vertical,
            launch_rod_pitch,
            launch_rod_azimuth,
        )
        return np.array([raw_manager, est_manager])

    def _get_first_packet(
        self, packet_type: RawDataPacket | EstimatedDataPacket
    ) -> RawDataPacket | EstimatedDataPacket:
        """
        Sets up the initial values for the estimated and raw data packets. This should only be
        called once, and all values will be approximate launch pad conditions.

        :param packet_type: either RawDataPacket or EstimatedDataPacket class objects. used as
            identifier.
        :return: data packet of the specified type with launch pad conditions.
        """
        packet = None
        if packet_type == RawDataPacket:
            scaled_accel = (
                self._raw_rotation_manager.calculate_compensated_accel(0.0, 0.0)
                / GRAVITY_METERS_PER_SECOND_SQUARED
            )
            packet = RawDataPacket(
                0,
                scaledAccelX=float(scaled_accel[0]),
                scaledAccelY=float(scaled_accel[1]),
                scaledAccelZ=float(scaled_accel[2]),
                scaledGyroX=0.0,
                scaledGyroY=0.0,
                scaledGyroZ=0.0,
                deltaVelX=0.0,
                deltaVelY=0.0,
                deltaVelZ=0.0,
                deltaThetaX=0.0,
                deltaThetaY=0.0,
                deltaThetaZ=0.0,
            )
        else:
            initial_quaternion = self._est_rotation_manager.calculate_imu_quaternions()
            compensated_accel = self._est_rotation_manager.calculate_compensated_accel(0.0, 0.0)
            linear_accel = self._est_rotation_manager.calculate_linear_accel(0.0, 0.0)
            gravity_vector = self._est_rotation_manager.gravity_vector
            packet = EstimatedDataPacket(
                0,
                estOrientQuaternionW=float(initial_quaternion[0]),
                estOrientQuaternionX=float(initial_quaternion[1]),
                estOrientQuaternionY=float(initial_quaternion[2]),
                estOrientQuaternionZ=float(initial_quaternion[3]),
                estPressureAlt=0.0,
                estAngularRateX=0.0,
                estAngularRateY=0.0,
                estAngularRateZ=0.0,
                estCompensatedAccelX=float(compensated_accel[0]),
                estCompensatedAccelY=float(compensated_accel[1]),
                estCompensatedAccelZ=float(compensated_accel[2]),
                estLinearAccelX=float(linear_accel[0]),
                estLinearAccelY=float(linear_accel[1]),
                estLinearAccelZ=float(linear_accel[2]),
                estGravityVectorX=float(gravity_vector[0]),
                estGravityVectorY=float(gravity_vector[1]),
                estGravityVectorZ=float(gravity_vector[2]),
            )

        return packet

    def generate_raw_data_packet(self) -> RawDataPacket:
        """
        Generates a raw data packet containing randomly generated data points.

        :return: RawDataPacket
        """
        # creating shorthand variables from config
        time_step = self._config.raw_time_step

        # If the simulation has just started, we want to just generate the initial raw packet
        # and initialize "self._last_" variables
        if self._last_raw_packet is None:
            self._last_raw_packet = self._get_first_packet(RawDataPacket)
            return self._last_raw_packet

        # updates the raw rotation manager, if we are after motor burn phase
        if (
            self._last_velocities[2] < self._max_vertical_velocity * MAX_VELOCITY_THRESHOLD
            and self._last_est_packet.timestamp > 1e9
        ):
            vertical_velocity_ratio = self._last_velocities[2] / self._max_vertical_velocity
            self._raw_rotation_manager.update_orientation(vertical_velocity_ratio)

        # calculates the timestamp for this packet (in seconds)
        next_timestamp = (self._last_raw_packet.timestamp / 1e9) + time_step

        # calculates the forces and vertical scaled acceleration
        forces = self._calculate_forces(next_timestamp, self._last_velocities)
        force_accelerations = forces / self._calculate_mass(next_timestamp)
        compensated_accel = self._raw_rotation_manager.calculate_compensated_accel(
            force_accelerations[0],
            force_accelerations[1],
        )
        scaled_accel = compensated_accel / GRAVITY_METERS_PER_SECOND_SQUARED

        # calculates vertical delta velocity, and gyro
        last_scaled_accel = np.array(
            [
                self._last_raw_packet.scaledAccelX,
                self._last_raw_packet.scaledAccelY,
                self._last_raw_packet.scaledAccelZ,
            ]
        )
        delta_velocity = (scaled_accel - last_scaled_accel) * GRAVITY_METERS_PER_SECOND_SQUARED
        delta_theta = self._raw_rotation_manager.calculate_delta_theta()
        scaled_gyro_vector = delta_theta / time_step

        # assembles the packet
        packet = RawDataPacket(
            timestamp=int(next_timestamp * 1e9),
            scaledAccelX=float(scaled_accel[0]),
            scaledAccelY=float(scaled_accel[1]),
            scaledAccelZ=float(scaled_accel[2]),
            scaledGyroX=float(scaled_gyro_vector[0]),
            scaledGyroY=float(scaled_gyro_vector[1]),
            scaledGyroZ=float(scaled_gyro_vector[2]),
            deltaVelX=float(delta_velocity[0]),
            deltaVelY=float(delta_velocity[1]),
            deltaVelZ=float(delta_velocity[2]),
            deltaThetaX=float(delta_theta[0]),
            deltaThetaY=float(delta_theta[1]),
            deltaThetaZ=float(delta_theta[2]),
        )

        # updates last raw data packet
        self._last_raw_packet = packet

        return packet

    def generate_estimated_data_packet(self) -> EstimatedDataPacket:
        """
        Generates an estimated data packet containing randomly generated data points.

        :return: EstimatedDataPacket
        """
        # creating shorthand variables from config
        time_step = self._config.est_time_step

        # If the simulation has just started, we want to just generate the initial estimated packet
        # and initialize "self._last_" variables
        if self._last_est_packet is None:
            self._last_est_packet = self._get_first_packet(EstimatedDataPacket)
            return self._last_raw_packet

        # updates the estimated rotation manager, if we are after motor burn phase
        vertical_velocity_ratio = self._last_velocities[2] / self._max_vertical_velocity
        if (
            self._last_velocities[2] < self._max_vertical_velocity * MAX_VELOCITY_THRESHOLD
            and self._last_est_packet.timestamp > 1e9
        ):
            self._est_rotation_manager.update_orientation(vertical_velocity_ratio)

        # calculates the timestamp for this packet (in seconds)
        next_timestamp = (self._last_est_packet.timestamp / 1e9) + time_step

        # calculates the forces and accelerations
        forces = self._calculate_forces(next_timestamp, self._last_velocities)
        force_accelerations = forces / self._calculate_mass(next_timestamp)
        compensated_accel = self._est_rotation_manager.calculate_compensated_accel(
            force_accelerations[0],
            force_accelerations[1],
        )

        # adds noise to compensated acceleration
        # the acceleration noise uses a linear regression model to apply more noise as the
        # magnitude of acceleration increases
        # The magnitude of noise is then split to all 3 directions of the compensated acceleration
        # vectors, to apply evenly.

        # First checks if we are in coast phase
        # TODO: don't repeat this check statement, as it is already done above. find cleaner way
        # to check current state in the sim.
        if (
            self._last_velocities[2] < self._max_vertical_velocity * MAX_VELOCITY_THRESHOLD
            and self._last_est_packet.timestamp > 1e9
        ):
            comp_accel_mag = np.linalg.norm(compensated_accel)
            comp_accel_noise_mag = get_random_value(
                self._config.rand_config.acceleration_noise_coefficients, comp_accel_mag
            )
            comp_accel_noise = (compensated_accel / comp_accel_mag) * comp_accel_noise_mag
            compensated_accel += comp_accel_noise

        # gets linear acceleration from the rotation manager
        linear_accel = self._est_rotation_manager.calculate_linear_accel(
            force_accelerations[0],
            force_accelerations[1],
        )

        # gets velocity and finds updated altitude
        vertical_velocity = self._calculate_velocities(compensated_accel, time_step)[2]
        new_altitude = self._last_est_packet.estPressureAlt + vertical_velocity * time_step

        delta_theta = self._est_rotation_manager.calculate_delta_theta()
        angular_rates = delta_theta / time_step

        quaternion = self._est_rotation_manager.calculate_imu_quaternions()
        packet = EstimatedDataPacket(
            timestamp=int(next_timestamp * 1e9),
            estOrientQuaternionW=float(quaternion[0]),
            estOrientQuaternionX=float(quaternion[1]),
            estOrientQuaternionY=float(quaternion[2]),
            estOrientQuaternionZ=float(quaternion[3]),
            estCompensatedAccelX=float(compensated_accel[0]),
            estCompensatedAccelY=float(compensated_accel[1]),
            estCompensatedAccelZ=float(compensated_accel[2]),
            estPressureAlt=float(new_altitude),
            estGravityVectorX=float(self._est_rotation_manager.gravity_vector[0]),
            estGravityVectorY=float(self._est_rotation_manager.gravity_vector[1]),
            estGravityVectorZ=float(self._est_rotation_manager.gravity_vector[2]),
            estAngularRateX=float(angular_rates[0]),
            estAngularRateY=float(angular_rates[1]),
            estAngularRateZ=float(angular_rates[2]),
            estLinearAccelX=float(linear_accel[0]),
            estLinearAccelY=float(linear_accel[1]),
            estLinearAccelZ=float(linear_accel[2]),
        )

        # updates last estimated packet
        self._last_est_packet = packet

        return packet

    def _calculate_velocities(self, comp_accel: npt.NDArray, time_diff: np.float64) -> np.float64:
        """
        Calculates the velocity vector of the rocket based on the compensated acceleration vector.
        Integrates that acceleration vector to get the velocity vector.

        :param: numpy array containing the compensated acceleration vector
        :return: the velocity vector of the rocket
        """
        # gets the rotated acceleration vector
        rotated_accel = self._est_rotation_manager.calculate_rotated_accelerations(comp_accel)
        # deadbands the wgs vertical part of the rotated acceleration
        rotated_accel[2] = deadband(
            rotated_accel[2] - GRAVITY_METERS_PER_SECOND_SQUARED,
            ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
        )

        # Integrate the rotated accelerations to get the velocity vector
        velocity_vector = self._last_velocities + rotated_accel * time_diff

        # updates the last velocity vector
        self._last_velocities = velocity_vector

        # updates max velocity
        self._max_vertical_velocity = max(velocity_vector[2], self._max_vertical_velocity)

        return velocity_vector

    def _calculate_forces(self, timestamp, velocity_vector) -> npt.NDArray:
        """
        Calculates the thrust force and drag force, and returns them in an array.

        :param timestamp: the timestamp of the rocket to calcuate the net forces at
        :param velocity_vector: numpy array containing velocity vector
        :return: a 2 element numpy array containing thrust force and drag force, respectively.
            Thrust is positive, drag is negative.
        """
        gradient = -6.5e-3  # troposphere gradient
        gas_constant = 287  # J/kg*K
        ratio_spec_heat = 1.4

        # last altitude
        altitude = self._last_est_packet.estPressureAlt
        # calculate the magnitude of velocity
        speed = np.linalg.norm(velocity_vector)
        # temperature using temperature gradient
        temp = self._config.air_temperature + 273.15 + gradient * altitude

        # air density formula, derived from ideal gas law
        air_density = 1.225 * (temp / (self._config.air_temperature + 273.15)) ** (
            -GRAVITY_METERS_PER_SECOND_SQUARED / (gas_constant * gradient) - 1
        )

        # using speed of sound to find mach number
        current_mach_number = speed / np.sqrt(ratio_spec_heat * gas_constant * temp)

        # gets the mach number vs drag coefficient lookup table in the config, depending on if
        # airbrakes are currently extended or not.
        mach_number_indices = (
            self._config.airbrakes_retracted_cd[0]
            if not self.is_airbrakes_extended
            else self._config.airbrakes_extended_cd[0]
        )
        drag_coefficient_lookup_table = (
            self._config.airbrakes_retracted_cd[1]
            if not self.is_airbrakes_extended
            else self._config.airbrakes_extended_cd[1]
        )

        # getting the current drag coefficient
        drag_coefficient = np.interp(
            current_mach_number,
            mach_number_indices,
            drag_coefficient_lookup_table,
        )

        thrust_force = 0.0
        # thrust force is non-zero if the timestamp is within the timeframe of
        # the motor burn
        if timestamp <= self._thrust_data[0][-1]:
            thrust_force = np.interp(timestamp, self._thrust_data[0], self._thrust_data[1])

        # reference area based on if airbrakes is extended or not
        reference_area = (
            self._config.reference_area
            if not self.is_airbrakes_extended
            else self._config.airbrakes_reference_area + self._config.reference_area
        )

        drag_force = 0.5 * air_density * reference_area * drag_coefficient * speed**2

        return np.array([thrust_force, drag_force])

    def _calculate_mass(self, timestamp: np.float64) -> np.float64:
        """
        Calculates the mass of the rocket at any given timestamp.

        The mass loss is found by calculating the mass flow rate using effective exhaust velocity.
        :param timestamp: current timestamp of the rocket, in seconds
        :return: the current mass of the rocket, in kilograms
        """
        # find current thrust
        current_thrust = np.interp(timestamp, self._thrust_data[0], self._thrust_data[1])
        # getting the thrust curve of the motor, up to current timestamp
        mask = self._thrust_data[0] <= timestamp
        time_values = np.append(self._thrust_data[0][mask], [timestamp])
        thrust_values = np.append(self._thrust_data[1][mask], [current_thrust])
        # Calculate the total impulse up to this timestamp as the integral of thrust over time
        current_total_impulse = np.trapezoid(thrust_values, time_values)

        # mass lost is current total impulse divided by effective exhaust velocity
        return self._config.rocket_mass - current_total_impulse / self._eff_exhaust_velocity
