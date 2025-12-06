"""
Module for interacting with the IMU (Inertial measurement unit) on the rocket.
"""

import contextlib
import multiprocessing

import mscl_rs
from faster_fifo import Queue  # ty: ignore[unresolved-import]  no type hints for this library

from airbrakes.constants import (
    BUFFER_SIZE_IN_BYTES,
    IMU_PROCESS_PRIORITY,
    IMU_TIMEOUT_SECONDS,
    MAX_QUEUE_SIZE,
)
from airbrakes.interfaces.base_imu import BaseIMU
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from airbrakes.utils import set_process_priority


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
        # Shared Queue which contains the latest data from the IMU. The MAX_QUEUE_SIZE is there
        # to prevent memory issues. Realistically, the queue size never exceeds 50 packets when
        # it's being logged.
        _queued_imu_packets: Queue[IMUDataPacket] = Queue(
            maxsize=MAX_QUEUE_SIZE,
            max_size_bytes=BUFFER_SIZE_IN_BYTES,
        )
        # Starts the process that fetches data from the IMU
        data_fetch_process = multiprocessing.Process(
            target=self._query_imu_for_data_packets, args=(port,), name="IMU Process"
        )
        super().__init__(data_fetch_process, _queued_imu_packets)

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE PROCESS -------------------------
    def _fetch_data_loop(self, port: str) -> None:  # pragma: no cover
        """
        Continuously fetch data packets from the IMU and process them.

        :param port: The serial port to connect to the IMU.
        """
        # Set the process priority really high, as we want to get the data from the IMU as fast as
        # possible:
        set_process_priority(IMU_PROCESS_PRIORITY)

        # Connect to the IMU and initialize the parser used for getting data packets
        parser = mscl_rs.SerialParser(port, timeout=IMU_TIMEOUT_SECONDS)
        parser.start()

        # This is a tight loop that fetches data from the IMU constantly. It looks ugly and written
        # the way as it is for performance reasons. Some of the optimizations implemented include
        # - using no functions inside the loop (this is typically 2x faster per packet)
        # - if-elif statements instead of a `match` / `setattr` / `hasattr` (2x-5x faster / packet)
        # - Using msgspec to serialize and deserialize the packets, which is faster than pickle
        # - High priority for the process
        while self._requested_to_run.value:
            # Retrieve data packets from the IMU.
            packets = parser.get_data_packets(block=True)

            self._imu_packets_per_cycle.value = len(packets)
            messages = []

            for packet in packets:
                if packet.packet_type == "raw":
                    imu_data_packet = RawDataPacket(
                        timestamp=packet.timestamp,
                        invalid_fields=packet.invalid_fields,
                        scaledAccelX=packet.scaled_accel[0],
                        scaledAccelY=packet.scaled_accel[1],
                        scaledAccelZ=packet.scaled_accel[2],
                        scaledGyroX=packet.scaled_gyro[0],
                        scaledGyroY=packet.scaled_gyro[1],
                        scaledGyroZ=packet.scaled_gyro[2],
                        scaledAmbientPressure=packet.scaled_ambient_pressure,
                        deltaThetaX=packet.delta_theta[0],
                        deltaThetaY=packet.delta_theta[1],
                        deltaThetaZ=packet.delta_theta[2],
                        deltaVelX=packet.delta_vel[0],
                        deltaVelY=packet.delta_vel[1],
                        deltaVelZ=packet.delta_vel[2],
                    )

                elif packet.packet_type == "estimated":
                    imu_data_packet = EstimatedDataPacket(
                        timestamp=packet.timestamp,
                        invalid_fields=packet.invalid_fields,
                        estOrientQuaternionW=packet.est_orient_quaternion[0],
                        estOrientQuaternionX=packet.est_orient_quaternion[1],
                        estOrientQuaternionY=packet.est_orient_quaternion[2],
                        estOrientQuaternionZ=packet.est_orient_quaternion[3],
                        estAttitudeUncertQuaternionW=packet.est_attitude_uncert_quaternion[0],
                        estAttitudeUncertQuaternionX=packet.est_attitude_uncert_quaternion[1],
                        estAttitudeUncertQuaternionY=packet.est_attitude_uncert_quaternion[2],
                        estAttitudeUncertQuaternionZ=packet.est_attitude_uncert_quaternion[3],
                        estAngularRateX=packet.est_angular_rate[0],
                        estAngularRateY=packet.est_angular_rate[1],
                        estAngularRateZ=packet.est_angular_rate[2],
                        estCompensatedAccelX=packet.est_compensated_accel[0],
                        estCompensatedAccelY=packet.est_compensated_accel[1],
                        estCompensatedAccelZ=packet.est_compensated_accel[2],
                        estLinearAccelX=packet.est_linear_accel[0],
                        estLinearAccelY=packet.est_linear_accel[1],
                        estLinearAccelZ=packet.est_linear_accel[2],
                        estGravityVectorX=packet.est_gravity_vector[0],
                        estGravityVectorY=packet.est_gravity_vector[1],
                        estGravityVectorZ=packet.est_gravity_vector[2],
                        estPressureAlt=packet.est_pressure_alt,
                    )
                else:
                    continue  # We never actually reach here, but keeping it just in case

                messages.append(imu_data_packet)

            self._queued_imu_packets.put_many(messages)

        parser.stop()

    def _query_imu_for_data_packets(self, port: str) -> None:
        """
        The loop that fetches data from the IMU.

        It runs in parallel with the main loop.
        :param port: the port that the IMU is connected to
        """
        self._running.value = True
        self._setup_queue_serialization_method()
        with contextlib.suppress(KeyboardInterrupt):
            self._fetch_data_loop(port)
        self._running.value = False
