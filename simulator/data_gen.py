"""Module that creates randomly generated data to sent to the simulator IMU"""

import csv
import random
from pathlib import Path

import numpy as np
import numpy.typing as npt
import yaml
from scipy.spatial.transform import Rotation as R

from airbrakes.data_handling.imu_data_packet import (
    EstimatedDataPacket,
    RawDataPacket,
)
from constants import ACCELERATION_NOISE_THRESHOLD, GRAVITY
from simulator.rotation_manager import RotationManager
from utils import deadband


class DataGenerator:
    """
    Uses config settings to generate realistic flight trajectories. Returns raw and
    estimated data points for the sim IMU to combine into data packets
    """

    __slots__ = (
        "_config",
        "_last_est_packet",
        "_last_raw_packet",
        "_last_velocity",
        "_thrust_data",
        "_vertical_index",
    )

    def __init__(self):
        """Initializes the data generator object"""
        self._last_est_packet: EstimatedDataPacket | None = None
        self._last_raw_packet: RawDataPacket | None = None
        self._last_velocity: np.float64 = np.float64(0.0)

        # loads the sim_config.yaml file
        config_path = Path("simulator/sim_config.yaml")
        with config_path.open(mode="r", newline="") as file:
            self._config: dict = yaml.safe_load(file)

        # loads thrust curve
        self._thrust_data: npt.NDArray = self._load_thrust_curve()

        # initializes the rotation manager with the launch pad conditions
        self._rotation_manager = self._get_rotation_manager()
        # finds the vertical index of the orientation. For example, if -y is vertical, the index
        # will be 1.
        self._vertical_index: np.int64 = np.nonzero(self._config["rocket_orientation"])[0][0]

    def _get_rotation_manager(self) -> RotationManager:
        # gets angle of attack and wind direction for the rocket
        rod_angle_of_attack = self._get_random("launch_rod_angle")
        wind_direction = self._get_random("wind_direction")
        # points the rocket into the wind, with some amount of error
        rod_direction = self._get_random("rod_direction_error") + (wind_direction-180)

        # initializes the rotation manager
        return RotationManager()

    def _get_random(self,identifier: str) -> np.float64:
        """
        Gets a random value for the selected identifier, using the standard deviation if given.

        :param identifier: string that matches a config variable in sim_config.yaml

        :return: float containing a random value for the selected identfier, between
            the bounds specified in the config
        """
        parameters = self._config[identifier]
        if len(parameters) == 3:
            # uses standard deviation to get random number
            mean = np.mean([parameters[0],parameters[1]])
            val = random.gauss(mean,parameters[2])
            # restricts the value to the bounds
            return np.max(parameters[0], np.min(parameters[1], val))
        # if no standard deviation is given, just return a uniform distribution
        return random.uniform(parameters[0],parameters[1])

    def _load_thrust_curve(self) -> npt.NDArray:
        """
        Loads the thrust curve from the motor specified in the configs.

        :return: numpy array containing tuples with the time and thrust at that time.
        """
        # gets the path of the csv based on the config file
        csv_path = Path(f"simulator/thrust_curves/{self._config["motor"]}.csv")

        # initializes the list for timestamps and thrust values
        motor_timestamps = [
            0,
        ]
        motor_thrusts = [
            0,
        ]

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

    def _get_first_packet(
            self,packet_type: RawDataPacket | EstimatedDataPacket
            ) -> RawDataPacket | EstimatedDataPacket:
        """
        Sets up the initial values for the estimated and raw data packets. This should
        only be called once, and all values will be approximate launch pad conditions.

        :param packet_type: either RawDataPacket or EstimatedDataPacket class objects.
            used as identifier.

        :return: data packet of the specified type with launch pad conditions.
        """
        orientation = self._config["rocket_orientation"]

        packet = None
        if packet_type == RawDataPacket:
            packet =  RawDataPacket(
                0,
                scaledAccelX=orientation[0],
                scaledAccelY=orientation[1],
                scaledAccelZ=orientation[2],
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
            initial_quaternion, _ = R.align_vectors([0, 0, -1], [orientation])
            initial_quaternion = R.as_quat(initial_quaternion, scalar_first=True)
            packet =  EstimatedDataPacket(
                0,
                estOrientQuaternionW=initial_quaternion[0],
                estOrientQuaternionX=initial_quaternion[1],
                estOrientQuaternionY=initial_quaternion[2],
                estOrientQuaternionZ=initial_quaternion[3],
                estCompensatedAccelX=GRAVITY * orientation[0],
                estCompensatedAccelY=GRAVITY * orientation[1],
                estCompensatedAccelZ=GRAVITY * orientation[2],
                estPressureAlt=0,
                estGravityVectorX=-GRAVITY * orientation[0],
                estGravityVectorY=-GRAVITY * orientation[1],
                estGravityVectorZ=-GRAVITY * orientation[2],
                estAngularRateX=0,
                estAngularRateY=0,
                estAngularRateZ=0,
            )

        return packet

    def generate_raw_data_packet(self) -> RawDataPacket:
        """
        Generates a raw data packet containing randomly generated data points

        :return: RawDataPacket
        """
        # creating shorthand variables from config
        time_step = self._config["raw_time_step"]
        orientation = self._config["rocket_orientation"]

        # If the simulation has just started, we want to just generate the initial raw packet
        # and initialize "self._last_" variables
        if self._last_raw_packet is None:
            self._last_raw_packet = self._get_first_packet(RawDataPacket)
            return self._last_raw_packet

        # calculates the timestamp for this packet (in seconds)
        next_timestamp = (self._last_raw_packet.timestamp/1e9) + time_step

        # calculates the net force and vertical scaled acceleration
        net_force = self._calculate_net_force(next_timestamp,self._last_velocity)
        vertical_scaled_accel = net_force / (self._config["rocket_mass"] * GRAVITY)

        # calculates vertical delta velocity
        last_vertical_scaled_accel = self._get_vertical_data_point("scaledAccel")
        vert_delta_v = (vertical_scaled_accel - last_vertical_scaled_accel) * GRAVITY * time_step

        packet =  RawDataPacket(
            next_timestamp * 1e9,
            scaledAccelX=vertical_scaled_accel * orientation[0],
            scaledAccelY=vertical_scaled_accel * orientation[1],
            scaledAccelZ=vertical_scaled_accel * orientation[2],
            scaledGyroX=0.0,
            scaledGyroY=0.0,
            scaledGyroZ=0.0,
            deltaVelX=vert_delta_v * orientation[0],
            deltaVelY=vert_delta_v * orientation[1],
            deltaVelZ=vert_delta_v * orientation[2],
            deltaThetaX=0.0,
            deltaThetaY=0.0,
            deltaThetaZ=0.0,
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
        time_step = self._config["est_time_step"]
        orientation = self._config["rocket_orientation"]

        # If the simulation has just started, we want to just generate the initial estimated packet
        # and initialize "self._last_" variables
        if self._last_est_packet is None:
            self._last_est_packet = self._get_first_packet(EstimatedDataPacket)
            return self._last_raw_packet

        # calculates the timestamp for this packet (in seconds)
        next_timestamp = (self._last_est_packet.timestamp/1e9) + time_step

        # calculates the net force and vertical accelerations
        net_force = self._calculate_net_force(next_timestamp,self._last_velocity)
        vertical_linear_accel = net_force / self._config["rocket_mass"]
        vertical_comp_accel = vertical_linear_accel + GRAVITY

        # gets vertical velocity and finds updated altitude
        vert_velocity = self._calculate_vertical_velocity(vertical_comp_accel, time_step)
        new_altitude = self._last_est_packet.estPressureAlt + vert_velocity * time_step

        # gets previous quaternion
        last_quat = np.array(
            [
                self._last_est_packet.estOrientQuaternionW,
                self._last_est_packet.estOrientQuaternionX,
                self._last_est_packet.estOrientQuaternionY,
                self._last_est_packet.estOrientQuaternionZ,
            ])

        packet = EstimatedDataPacket(
            next_timestamp * 1e9,
            estOrientQuaternionW=last_quat[0],
            estOrientQuaternionX=last_quat[1],
            estOrientQuaternionY=last_quat[2],
            estOrientQuaternionZ=last_quat[3],
            estCompensatedAccelX=vertical_comp_accel * orientation[0],
            estCompensatedAccelY=vertical_comp_accel * orientation[1],
            estCompensatedAccelZ=vertical_comp_accel * orientation[2],
            estPressureAlt=new_altitude,
            estGravityVectorX=-GRAVITY * orientation[0],
            estGravityVectorY=-GRAVITY * orientation[1],
            estGravityVectorZ=-GRAVITY * orientation[2],
            estAngularRateX=0,
            estAngularRateY=0,
            estAngularRateZ=0,
        )

        # updates last estimated packet
        self._last_est_packet = packet

        return packet

    def _calculate_vertical_velocity(self, acceleration, time_diff) -> np.float64:
        """
        Calculates the velocity of the rocket based on the compensated acceleration.
        Integrates that acceleration to get the velocity.

        :return: the velocity of the rocket
        """
        # deadbands the acceleration
        acceleration = deadband(acceleration - GRAVITY, ACCELERATION_NOISE_THRESHOLD)

        # Integrate the acceleration to get the velocity
        vertical_velocity = self._last_velocity + acceleration * time_diff

        # updates the last vertical velocity
        self._last_velocity = vertical_velocity

        return vertical_velocity

    def _calculate_net_force(self, timestamp, velocity) -> np.float64:
        """
        Calculates the drag force, thrust force, and weight, and sums them.

        :param timestamp: the timestamp of the rocket to calcuate the net forces at
        :param velocity: the vertical velocity at the given instant

        :return: float containing the net force. Thrust is positive, drag and weight is negative.
        """
        # we could probably actually calculate air density, maybe we set temperature as constant?
        air_density = 1.1
        reference_area = self._config["reference_area"]
        drag_coefficient = self._config["drag_coefficient"]
        rocket_mass = self._config["rocket_mass"]

        drag_force =  0.5 * air_density * reference_area * drag_coefficient * velocity**2
        weight_force = GRAVITY * rocket_mass
        thrust_force = 0.0

        # thrust force is non-zero if the timestamp is within the timeframe of
        # the motor burn
        if timestamp <= self._thrust_data[0][-1]:
            thrust_force = np.interp(
                timestamp, self._thrust_data[0], self._thrust_data[1]
            )
        return thrust_force - weight_force - drag_force

    def _get_vertical_data_point(self,string_identifier: str) -> np.float64:
        """
        gets the last vertical data point specified from a vector data attribute by using IMU
        orientation in config

        :param string_identfier: a string representing the exact attribute name of the data packet

        :return: float containing the specified data point
        """
        # Dynamically retrieve x, y, z components based on the identifier
        values = [
            getattr(self._last_raw_packet, f"{string_identifier}X", None),
            getattr(self._last_raw_packet, f"{string_identifier}Y", None),
            getattr(self._last_raw_packet, f"{string_identifier}Z", None),
        ]

        # Just an edge case, but I really hope this never happens
        if any(value is None for value in values):
            raise AttributeError(
                f"Could not find all components for identifier '{string_identifier}'."
                )

        return values[self._vertical_index]
