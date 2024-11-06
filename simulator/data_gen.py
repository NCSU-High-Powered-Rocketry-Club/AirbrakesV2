"""Module that creates randomly generated data to sent to the simulator IMU"""

import csv
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
from utils import deadband


class DataGenerator:
    """
    Uses config settings to generate realistic flight trajectories. Returns raw and
    estimated data points for the sim IMU to combine into data packets
    """

    __slots__ = (
        "_config",
        "_current_timestamp",
        "_last_est_packet",
        "_last_raw_packet",
        "_last_velocity",
        "_thrust_data",
        "_vertical_index",
    )

    def __init__(self):
        """Initializes the data generator object"""
        self._current_timestamp: np.float64 = np.float64(0.0)
        self._last_est_packet: EstimatedDataPacket | None = None
        self._last_raw_packet: RawDataPacket | None = None
        self._last_velocity: np.float64 = np.float64(0.0)

        # loads the sim_config.yaml file
        config_path = Path("simulator/sim_config.yaml")
        with config_path.open(mode="r", newline="") as file:
            self._config: dict = yaml.safe_load(file)

        # finds the vertical index of the orientation. For example, if -y is vertical, the index
        # will be 1.
        self._vertical_index: np.int64 = np.nonzero(self._config["rocket_orientation"])[0][0]
        self._thrust_data: npt.NDArray = self._load_thrust_curve()

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

    def _first_update(self) -> npt.NDArray:
        """
        Sets up the initial values for the estimated and raw data packets. This should
        only be called once, and all values will be approximate launch pad conditions.

        :return: numpy array containing a raw data packet and an estimated data packet
            respectively, immitating initial conditions on the launch pad.
        """
        orientation = self._config["rocket_orientation"]
        initial_quaternion, _ = R.align_vectors([0, 0, -1], [orientation])
        initial_quaternion = R.as_quat(initial_quaternion, scalar_first=True)

        return np.array(
            [
                RawDataPacket(
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
                ),
                EstimatedDataPacket(
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
                ),
            ]
        )

    def generate_data_packet(self) -> npt.NDArray:
        """
        Generates data points and sends to queue

        :return: Numpy list containing a raw data packet, an estimated data packet, or both.
        """
        # gets the next timestamp
        next_timestamp = self.update_timestamp(self._current_timestamp)
        # If the simulation has just started, we want to just generate the initial data points
        # and initialize "self._last_" variables
        if any(packet is None for packet in [self._last_est_packet, self._last_raw_packet]):
            self._last_raw_packet, self._last_est_packet = self._first_update()
            self._current_timestamp = next_timestamp
            return np.array([self._last_raw_packet, self._last_est_packet])

        raw_time_step = self._config["raw_time_step"]
        est_time_step = self._config["est_time_step"]

        # creates a boolean array to indicate whether the next timestamp will have a raw
        # data packet, an estimated data packet, or both.
        packet_type_flag = np.array(
            [
                any(np.isclose(next_timestamp % raw_time_step, [0, raw_time_step])),
                any(np.isclose(next_timestamp % est_time_step, [0, est_time_step])),
            ]
        )

        # just as a short-hand
        orientation = self._config["rocket_orientation"]

        # finds acceleration from thrust curve data, if the timestamp is before the cutoff time
        # of the motor
        if next_timestamp <= self._thrust_data[0][-1]:
            interpreted_thrust = np.interp(
                next_timestamp, self._thrust_data[0], self._thrust_data[1]
            )
            vertical_linear_accel = interpreted_thrust / self._config["rocket_mass"]

        new_packets = np.array([None, None])

        # assembles the raw data packet
        if packet_type_flag[0]:
            # scaled acceleration is compensated, but divided by gravity. On launch pad, the
            # vertical sacled acceleration will be -1.00 (if negative is vertical).
            # this value should always be positive though (during motor burn)
            vert_scaled_accel = 1 + vertical_linear_accel / GRAVITY

            # gets the last vertical scaled accel, flips depending on the vertical index
            last_vert_scaled_accel = [
                self._last_raw_packet.scaledAccelX,
                self._last_raw_packet.scaledAccelY,
                self._last_raw_packet.scaledAccelZ,
            ][self._vertical_index]

            # finds the vertical delta velocity
            vert_delta_v = GRAVITY * (vert_scaled_accel - last_vert_scaled_accel) * raw_time_step

            raw_data_packet = RawDataPacket(
                next_timestamp * 1e9,
                scaledAccelX=vert_scaled_accel * orientation[0],
                scaledAccelY=vert_scaled_accel * orientation[1],
                scaledAccelZ=vert_scaled_accel * orientation[2],
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
            # appends to array
            new_packets[0] = raw_data_packet

            # updates last packet
            self._last_raw_packet = raw_data_packet

        # Assembles the estimated data packet
        if packet_type_flag[1]:
            # default value is positive during motor burn
            vert_comp_accel = vertical_linear_accel + GRAVITY

            # gets vertical velocity and finds updated altitude
            vert_velocity = self._calculate_vertical_velocity(vert_comp_accel, est_time_step)
            last_altitude = self._last_est_packet.estPressureAlt
            new_altitude = last_altitude + vert_velocity * est_time_step

            # gets previous quaternion
            last_quat = np.array(
                [
                    self._last_est_packet.estOrientQuaternionW,
                    self._last_est_packet.estOrientQuaternionX,
                    self._last_est_packet.estOrientQuaternionY,
                    self._last_est_packet.estOrientQuaternionZ,
                ]
            )

            est_data_packet = EstimatedDataPacket(
                next_timestamp * 1e9,
                estOrientQuaternionW=last_quat[0],
                estOrientQuaternionX=last_quat[1],
                estOrientQuaternionY=last_quat[2],
                estOrientQuaternionZ=last_quat[3],
                estCompensatedAccelX=vert_comp_accel * orientation[0],
                estCompensatedAccelY=vert_comp_accel * orientation[1],
                estCompensatedAccelZ=vert_comp_accel * orientation[2],
                estPressureAlt=new_altitude,
                estGravityVectorX=-GRAVITY * orientation[0],
                estGravityVectorY=-GRAVITY * orientation[1],
                estGravityVectorZ=-GRAVITY * orientation[2],
                estAngularRateX=0,
                estAngularRateY=0,
                estAngularRateZ=0,
            )

            # appends to array
            new_packets[1] = est_data_packet

            # updates last packet
            self._last_est_packet = est_data_packet

        # updates the timestamp
        self._current_timestamp = next_timestamp

        return new_packets

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

    def update_timestamp(self, current_timestamp: np.float64) -> np.float64:
        """
        Updates the current timestamp of the data generator, based off time step defined in config.
        Will also determine if the next timestamp will be a raw packet, estimated packet, or both.

        :param current_timestamp: the current timestamp of the simulation

        :return: the updated current timestamp, rounded to 3 decimals
        """

        # finding whether the raw or estimated data packets have a lower time_step
        lowest_dt = min(self._config["raw_time_step"], self._config["est_time_step"])
        highest_dt = max(self._config["raw_time_step"], self._config["est_time_step"])

        # checks if current time is a multiple of the highest and/or lowest time step
        at_low = any(np.isclose(current_timestamp % lowest_dt, [0, lowest_dt]))
        at_high = any(np.isclose(current_timestamp % highest_dt, [0, highest_dt]))

        # If current timestamp is a multiple of both, the next timestamp will be the
        # the current timestamp + the lower time steps
        if all([at_low, at_high]):
            return np.round(current_timestamp + lowest_dt, 3)

        # If timestamp is a multiple of just the lowest time step, the next will be
        # either current + lowest, or the next timestamp that is divisible by the highest
        if at_low and not at_high:
            dt = min(lowest_dt, highest_dt - (current_timestamp % highest_dt))
            return np.round(current_timestamp + dt, 3)

        # If timestamp is a multiple of only the highest time step, the next will
        # always be the next timestamp that is divisible by the lowest
        if at_high and not at_low:
            return np.round(current_timestamp + lowest_dt - (current_timestamp % lowest_dt), 3)

        # This would happen if the input current timestamp is not a multiple of the raw
        # or estimated time steps, or if there is a rounding/floating point error.
        raise ValueError("Could not update timestamp, time stamp is invalid")
