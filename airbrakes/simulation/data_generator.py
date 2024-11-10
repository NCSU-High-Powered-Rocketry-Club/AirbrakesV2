"""Module that creates randomly generated data to sent to the simulation IMU"""

import csv
import random
from pathlib import Path

import numpy as np
import numpy.typing as npt

from airbrakes.data_handling.imu_data_packet import (
    EstimatedDataPacket,
    RawDataPacket,
)
from airbrakes.simulation.rotation_manager import RotationManager
from airbrakes.simulation.sim_config import SimulationConfig
from constants import ACCELERATION_NOISE_THRESHOLD, GRAVITY, MAX_VELOCITY_THRESHOLD
from utils import deadband


class DataGenerator:
    """
    Uses config settings to generate realistic flight trajectories. Returns raw and
    estimated data points for the sim IMU to combine into data packets
    """

    __slots__ = (
        "_config",
        "_est_rotation_manager",
        "_last_est_packet",
        "_last_raw_packet",
        "_last_velocities",
        "_max_velocity",
        "_raw_rotation_manager",
        "_thrust_data",
        "_vertical_index",
    )

    def __init__(self, config: SimulationConfig):
        """
        Initializes the data generator object with the provided configuration
        :param config: the configuration object for the simulation
        """

        self._config = config

        self._last_est_packet: EstimatedDataPacket | None = None
        self._last_raw_packet: RawDataPacket | None = None
        self._last_velocities: npt.NDArray = np.array([0.0, 0.0, 0.0])
        self._max_velocity: np.float64 = np.float64(0.1)

        # loads thrust curve
        self._thrust_data: npt.NDArray = self._load_thrust_curve()

        # initializes the rotation manager with the launch pad conditions
        raw_manager, est_manager = self._get_rotation_managers()
        self._raw_rotation_manager: RotationManager = raw_manager
        self._est_rotation_manager: RotationManager = est_manager

        # finds the vertical index of the orientation. For example, if -y is vertical, the index
        # will be 1.
        self._vertical_index: np.int64 = np.nonzero(self._config.rocket_orientation)[0][0]

    @property
    def velocities(self) -> npt.NDArray:
        """Returns the last calculated velocity of the rocket"""
        return self._last_velocities

    def _get_random(self, identifier: str) -> np.float64:
        """
        Gets a random value for the selected identifier, using the standard deviation if given.
        :param identifier: string that matches a config variable in sim_config.yaml
        :return: float containing a random value for the selected identifier, between
        the bounds specified in the config
        """
        parameters = getattr(self._config, identifier)
        if len(parameters) == 1:
            return parameters[0]
        if len(parameters) == 3:
            # uses standard deviation to get random number
            mean = float(np.mean([parameters[0], parameters[1]]))
            val = random.gauss(mean, parameters[2])
            # restricts the value to the bounds
            return np.max(parameters[0], np.min(parameters[1], val))
        # if no standard deviation is given, just return a uniform distribution
        return random.uniform(parameters[0], parameters[1])

    def _load_thrust_curve(self) -> npt.NDArray:
        """
        Loads the thrust curve from the motor specified in the configs.
        :return: numpy array containing tuples with the time and thrust at that time.
        """
        # gets the path of the csv based on the config file
        csv_path = Path(f"airbrakes/simulation/thrust_curves/{self._config.motor}.csv")

        # initializes the list for timestamps and thrust values
        motor_timestamps = [0]
        motor_thrusts = [0]

        start_flag = False  # flag to identify when the metadata/header rows are skipped

        with csv_path.open(mode="r", newline="") as thrust_csv:
            reader = csv.reader(thrust_csv)

            for row in reader:
                # Start appending data only after the header row
                if row == ["Time (s)", "Thrust (N)"]:
                    start_flag = True
                    continue  # Skip header row itself

                if start_flag:
                    # Convert time and thrust values to floats and append as a tuple
                    time = float(row[0])
                    thrust = float(row[1])
                    motor_timestamps.append(time)
                    motor_thrusts.append(thrust)

        return np.array([motor_timestamps, motor_thrusts])

    def _get_rotation_managers(self) -> npt.NDArray:
        """
        Creates and initializes both rotation managers that will be used to contain any rotation
        related math and methods for the raw and estimated data.

        :return: a 2 element array containing the raw rotation manager and the estimated rotation
        manager, respectively.
        """
        launch_rod_angle = self._get_random("launch_rod_angle")
        launch_rod_direction = self._get_random("launch_rod_direction")
        raw_manager = RotationManager(
            self._config.rocket_orientation,
            launch_rod_angle,
            launch_rod_direction,
        )
        est_manager = RotationManager(
            self._config.rocket_orientation,
            launch_rod_angle,
            launch_rod_direction,
        )
        return np.array([raw_manager, est_manager])

    def _get_first_packet(
        self, packet_type: RawDataPacket | EstimatedDataPacket
    ) -> RawDataPacket | EstimatedDataPacket:
        """
        Sets up the initial values for the estimated and raw data packets. This should
        only be called once, and all values will be approximate launch pad conditions.

        :param packet_type: either RawDataPacket or EstimatedDataPacket class objects.
            used as identifier.

        :return: data packet of the specified type with launch pad conditions.
        """

        packet = None
        if packet_type == RawDataPacket:
            scaled_accel = (
                self._raw_rotation_manager.calculate_compensated_accel(0.0, 0.0) / GRAVITY
            )
            packet = RawDataPacket(
                0,
                scaledAccelX=scaled_accel[0],
                scaledAccelY=scaled_accel[1],
                scaledAccelZ=scaled_accel[2],
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
                estOrientQuaternionW=initial_quaternion[0],
                estOrientQuaternionX=initial_quaternion[1],
                estOrientQuaternionY=initial_quaternion[2],
                estOrientQuaternionZ=initial_quaternion[3],
                estPressureAlt=0,
                estAngularRateX=0,
                estAngularRateY=0,
                estAngularRateZ=0,
                estCompensatedAccelX=compensated_accel[0],
                estCompensatedAccelY=compensated_accel[1],
                estCompensatedAccelZ=compensated_accel[2],
                estLinearAccelX=linear_accel[0],
                estLinearAccelY=linear_accel[1],
                estLinearAccelZ=linear_accel[2],
                estGravityVectorX=gravity_vector[0],
                estGravityVectorY=gravity_vector[1],
                estGravityVectorZ=gravity_vector[2],
            )

        return packet

    def generate_raw_data_packet(self) -> RawDataPacket:
        """
        Generates a raw data packet containing randomly generated data points

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
            self._last_velocities[2]
            < self._max_velocity - self._last_velocities[2] * MAX_VELOCITY_THRESHOLD
            and self._last_est_packet.timestamp > 1e9
        ):
            velocity_ratio = self._last_velocities[2] / self._max_velocity
            self._raw_rotation_manager.update_orientation(time_step, velocity_ratio)

        # calculates the timestamp for this packet (in seconds)
        next_timestamp = (self._last_raw_packet.timestamp / 1e9) + time_step

        # calculates the forces and vertical scaled acceleration
        forces = self._calculate_forces(next_timestamp, self._last_velocities)
        force_accelerations = forces / self._config.rocket_mass
        compensated_accel = self._raw_rotation_manager.calculate_compensated_accel(
            force_accelerations[0],
            force_accelerations[1],
        )
        scaled_accel = compensated_accel / GRAVITY

        # calculates vertical delta velocity, and gyro
        last_scaled_accel = np.array(
            [
                self._last_raw_packet.scaledAccelX,
                self._last_raw_packet.scaledAccelY,
                self._last_raw_packet.scaledAccelZ,
            ]
        )
        delta_velocity = (scaled_accel - last_scaled_accel) * GRAVITY
        delta_theta = self._raw_rotation_manager.calculate_delta_theta()
        scaled_gyro_vector = delta_theta / time_step

        # assembles the packet
        packet = RawDataPacket(
            next_timestamp * 1e9,
            scaledAccelX=scaled_accel[0],
            scaledAccelY=scaled_accel[1],
            scaledAccelZ=scaled_accel[2],
            scaledGyroX=scaled_gyro_vector[0],
            scaledGyroY=scaled_gyro_vector[1],
            scaledGyroZ=scaled_gyro_vector[2],
            deltaVelX=delta_velocity[0],
            deltaVelY=delta_velocity[1],
            deltaVelZ=delta_velocity[2],
            deltaThetaX=delta_theta[0],
            deltaThetaY=delta_theta[1],
            deltaThetaZ=delta_theta[2],
        )

        # updates last raw data packet
        self._last_raw_packet = packet

        return packet

    def generate_estimated_data_packet(self) -> EstimatedDataPacket:
        """
        Generates an estimated data packet containing randomly generated data points

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
        if (
            self._last_velocities[2]
            < self._max_velocity - self._last_velocities[2] * MAX_VELOCITY_THRESHOLD
            and self._last_est_packet.timestamp > 1e9
        ):
            velocity_ratio = self._last_velocities[2] / self._max_velocity
            self._est_rotation_manager.update_orientation(time_step, velocity_ratio)

        # calculates the timestamp for this packet (in seconds)
        next_timestamp = (self._last_est_packet.timestamp / 1e9) + time_step

        # calculates the forces and accelerations
        forces = self._calculate_forces(next_timestamp, self._last_velocities)
        force_accelerations = forces / self._config.rocket_mass
        compensated_accel = self._est_rotation_manager.calculate_compensated_accel(
            force_accelerations[0],
            force_accelerations[1],
        )
        linear_accel = self._est_rotation_manager.calculate_linear_accel(
            force_accelerations[0],
            force_accelerations[1],
        )

        # gets velocity and finds updated altitude
        vert_velocity = self._calculate_velocities(compensated_accel, time_step)[2]
        new_altitude = self._last_est_packet.estPressureAlt + vert_velocity * time_step

        delta_theta = self._est_rotation_manager.calculate_delta_theta()
        angular_rates = delta_theta / time_step

        quaternion = self._est_rotation_manager.calculate_imu_quaternions()

        packet = EstimatedDataPacket(
            next_timestamp * 1e9,
            estOrientQuaternionW=quaternion[0],
            estOrientQuaternionX=quaternion[1],
            estOrientQuaternionY=quaternion[2],
            estOrientQuaternionZ=quaternion[3],
            estCompensatedAccelX=compensated_accel[0],
            estCompensatedAccelY=compensated_accel[1],
            estCompensatedAccelZ=compensated_accel[2],
            estPressureAlt=new_altitude,
            estGravityVectorX=self._est_rotation_manager.gravity_vector[0],
            estGravityVectorY=self._est_rotation_manager.gravity_vector[1],
            estGravityVectorZ=self._est_rotation_manager.gravity_vector[2],
            estAngularRateX=angular_rates[0],
            estAngularRateY=angular_rates[1],
            estAngularRateZ=angular_rates[2],
            estLinearAccelX=linear_accel[0],
            estLinearAccelY=linear_accel[1],
            estLinearAccelZ=linear_accel[2],
        )

        # updates last estimated packet
        self._last_est_packet = packet

        return packet

    def _calculate_velocities(self, comp_accel: npt.NDArray, time_diff: np.float64) -> np.float64:
        """
        Calculates the velocity of the rocket based on the compensated acceleration.
        Integrates that acceleration to get the velocity.

        :param: numpy array containing the compensated acceleration vector

        :return: the velocity of the rocket
        """
        # gets the rotated acceleration vector
        accelerations = self._est_rotation_manager.calculate_rotated_accelerations(comp_accel)
        # gets vertical part of the gravity vector
        accelerations[2] = deadband(accelerations[2] - GRAVITY, ACCELERATION_NOISE_THRESHOLD)

        # Integrate the accelerations to get the velocity
        velocities = self._last_velocities + accelerations * time_diff

        # updates the last vertical velocity
        self._last_velocities = velocities

        # updates max velocity
        self._max_velocity = max(velocities[2], self._max_velocity)

        return velocities

    def _calculate_forces(self, timestamp, velocities) -> npt.NDArray:
        """
        Calculates the thrust force and drag force, and returns them in an array

        :param timestamp: the timestamp of the rocket to calcuate the net forces at
        :param velocities: numpy array containing the x, y, and z velocities

        :return: a 2 element numpy array containing thrust force and drag force, respectively.
        Thrust is positive, drag is negative.
        """
        # calculate the magnitude of velocity
        speed = np.linalg.norm(velocities)

        # we could probably actually calculate air density, maybe we set temperature as constant?
        air_density = 1.1

        thrust_force = 0.0
        drag_force = 0.5 * air_density * self._config.reference_area * self._config.drag_coefficient * speed**2

        # thrust force is non-zero if the timestamp is within the timeframe of
        # the motor burn
        if timestamp <= self._thrust_data[0][-1]:
            thrust_force = np.interp(timestamp, self._thrust_data[0], self._thrust_data[1])
        return np.array([thrust_force, drag_force])
