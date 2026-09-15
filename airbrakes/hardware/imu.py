"""
Module for interacting with the IMU (Inertial measurement unit) on the rocket.
"""

import queue
import threading

import mscl_rs

from airbrakes.base_classes.base_imu import BaseIMU
from airbrakes.constants import (
    IMU_TIMEOUT_SECONDS,
)
from airbrakes.data_handling.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)


class IMU(BaseIMU):
    """
    Represents the IMU on the rocket. It's used to get the current motion of the rocket, including
    the acceleration, rotation, and position. This is used to interact with the data collected by
    the Parker-LORD 3DMCX5-AR. (https://www.microstrain.com/inertial-sensors/3dm-cx5-15).

    Here is the setup docs: https://github.com/LORD-MicroStrain/MSCL/blob/master/HowToUseMSCL.md
    Here is the software for configuring the IMU: https://www.microstrain.com/software/sensorconnect
    """

    __slots__ = ()

    def __init__(self, port: str) -> None:
        """
        Initializes the object that interacts with the physical IMU connected to the pi.

        :param port: the port that the IMU is connected to
        """
        # Shared Queue which contains the latest data from the IMU.
        _queued_imu_packets: queue.SimpleQueue[IMUDataPacket] = queue.SimpleQueue()
        # Initialize the thread that fetches data from the IMU
        data_fetch_thread = threading.Thread(
            target=self._query_imu_for_data_packets,
            args=(port,),
            name="IMU Thread",
            daemon=True,
        )
        super().__init__(data_fetch_thread, _queued_imu_packets)

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE THREAD -------------------------
    def _fetch_data_loop(self, port: str) -> None:  # pragma: no cover
        """
        Continuously fetch data packets from the IMU and process them.

        :param port: The serial port to connect to the IMU.
        """
        # Connect to the IMU and initialize the parser used for getting data packets
        parser = mscl_rs.SerialParser(port, timeout=IMU_TIMEOUT_SECONDS)
        parser.start()

        # This is a tight loop that fetches data from the IMU constantly. It looks ugly and written
        # the way as it is for performance reasons. Some of the optimizations implemented include
        # - using no functions inside the loop (this is typically 2x faster per packet)
        # - if-elif statements instead of a `match` / `setattr` / `hasattr` (2x-5x faster / packet)
        # - Using msgspec to serialize and deserialize the packets, which is faster than pickle
        # - High priority for the main process
        while self._requested_to_run.is_set():
            # Retrieve data packets from the IMU.
            packets = parser.get_data_packets(block=True)

            self._imu_packets_per_cycle = len(packets)

            for packet in packets:
                if packet.packet_type == "raw":
                    scaled_accel = packet.scaled_accel
                    scaled_gyro = packet.scaled_gyro
                    delta_theta = packet.delta_theta
                    delta_vel = packet.delta_vel
                    imu_data_packet = RawDataPacket(
                        timestamp=packet.timestamp,
                        invalid_fields=packet.invalid_fields,
                        scaledAccelX=scaled_accel[0] if scaled_accel is not None else None,
                        scaledAccelY=scaled_accel[1] if scaled_accel is not None else None,
                        scaledAccelZ=scaled_accel[2] if scaled_accel is not None else None,
                        scaledGyroX=scaled_gyro[0] if scaled_gyro is not None else None,
                        scaledGyroY=scaled_gyro[1] if scaled_gyro is not None else None,
                        scaledGyroZ=scaled_gyro[2] if scaled_gyro is not None else None,
                        scaledAmbientPressure=packet.scaled_ambient_pressure,
                        deltaThetaX=delta_theta[0] if delta_theta is not None else None,
                        deltaThetaY=delta_theta[1] if delta_theta is not None else None,
                        deltaThetaZ=delta_theta[2] if delta_theta is not None else None,
                        deltaVelX=delta_vel[0] if delta_vel is not None else None,
                        deltaVelY=delta_vel[1] if delta_vel is not None else None,
                        deltaVelZ=delta_vel[2] if delta_vel is not None else None,
                    )

                elif packet.packet_type == "estimated":
                    orientation = packet.est_orient_quaternion
                    uncertainty = packet.est_attitude_uncert_quaternion
                    angular_rate = packet.est_angular_rate
                    compensated_acceleration = packet.est_compensated_accel
                    linear_acceleration = packet.est_linear_accel
                    gravity_vector = packet.est_gravity_vector
                    imu_data_packet = EstimatedDataPacket(
                        timestamp=packet.timestamp,
                        invalid_fields=packet.invalid_fields,
                        estOrientQuaternionW=orientation[0] if orientation is not None else None,
                        estOrientQuaternionX=orientation[1] if orientation is not None else None,
                        estOrientQuaternionY=orientation[2] if orientation is not None else None,
                        estOrientQuaternionZ=orientation[3] if orientation is not None else None,
                        estAttitudeUncertQuaternionW=uncertainty[0]
                        if uncertainty is not None
                        else None,
                        estAttitudeUncertQuaternionX=uncertainty[1]
                        if uncertainty is not None
                        else None,
                        estAttitudeUncertQuaternionY=uncertainty[2]
                        if uncertainty is not None
                        else None,
                        estAttitudeUncertQuaternionZ=uncertainty[3]
                        if uncertainty is not None
                        else None,
                        estAngularRateX=angular_rate[0] if angular_rate is not None else None,
                        estAngularRateY=angular_rate[1] if angular_rate is not None else None,
                        estAngularRateZ=angular_rate[2] if angular_rate is not None else None,
                        estCompensatedAccelX=(
                            compensated_acceleration[0]
                            if compensated_acceleration is not None
                            else None
                        ),
                        estCompensatedAccelY=(
                            compensated_acceleration[1]
                            if compensated_acceleration is not None
                            else None
                        ),
                        estCompensatedAccelZ=(
                            compensated_acceleration[2]
                            if compensated_acceleration is not None
                            else None
                        ),
                        estLinearAccelX=(
                            linear_acceleration[0] if linear_acceleration is not None else None
                        ),
                        estLinearAccelY=(
                            linear_acceleration[1] if linear_acceleration is not None else None
                        ),
                        estLinearAccelZ=(
                            linear_acceleration[2] if linear_acceleration is not None else None
                        ),
                        estGravityVectorX=(
                            gravity_vector[0] if gravity_vector is not None else None
                        ),
                        estGravityVectorY=(
                            gravity_vector[1] if gravity_vector is not None else None
                        ),
                        estGravityVectorZ=(
                            gravity_vector[2] if gravity_vector is not None else None
                        ),
                        estPressureAlt=packet.est_pressure_alt,
                    )
                else:
                    continue  # We never actually reach here, but keeping it just in case

                self._queued_imu_packets.put_nowait(imu_data_packet)

        parser.stop()

    def _query_imu_for_data_packets(self, port: str) -> None:
        """
        The loop that fetches data from the IMU.

        It runs in parallel with the main loop.
        :param port: the port that the IMU is connected to
        """
        self._running.set()
        self._fetch_data_loop(port)
        self._running.clear()
