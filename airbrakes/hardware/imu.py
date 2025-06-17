"""
Module for interacting with the IMU (Inertial measurement unit) on the rocket.
"""

import contextlib
import multiprocessing

import msgspec
import msgspec.msgpack
from faster_fifo import Queue  # ty: ignore[unresolved-import]  no type hints for this library
from python_mscl import mscl

from airbrakes.constants import (
    AMBIENT_PRESSURE_QUALIFIER,
    ATTITUDE_UNCERT_QUALIFIER,
    BUFFER_SIZE_IN_BYTES,
    DELTA_THETA_FIELD,
    DELTA_VEL_FIELD,
    EST_ANGULAR_RATE_FIELD,
    EST_ATTITUDE_UNCERT_FIELD,
    EST_COMPENSATED_ACCEL_FIELD,
    EST_GRAVITY_VECTOR_FIELD,
    EST_LINEAR_ACCEL_FIELD,
    EST_ORIENT_QUATERNION_FIELD,
    EST_PRESSURE_ALT_FIELD,
    ESTIMATED_DESCRIPTOR_SET,
    IMU_PROCESS_PRIORITY,
    MAX_QUEUE_SIZE,
    PRESSURE_ALT_QUALIFIER,
    RAW_DESCRIPTOR_SET,
    SCALED_ACCEL_FIELD,
    SCALED_AMBIENT_PRESSURE_FIELD,
    SCALED_GYRO_FIELD,
    X_QUALIFIER,
    Y_QUALIFIER,
    Z_QUALIFIER,
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
        # We will never run the actual IMU on Windows, so we can use the faster_fifo library always:
        msgpack_encoder = msgspec.msgpack.Encoder()
        msgpack_decoder = msgspec.msgpack.Decoder(type=EstimatedDataPacket | RawDataPacket)

        _queued_imu_packets: Queue[IMUDataPacket] = Queue(
            maxsize=MAX_QUEUE_SIZE,
            max_size_bytes=BUFFER_SIZE_IN_BYTES,
            dumps=msgpack_encoder.encode,
            loads=msgpack_decoder.decode,
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

        # Connect to the IMU and initialize the node used for getting data packets
        connection = mscl.Connection.Serial(port)
        node = mscl.InertialNode(connection)
        packet: mscl.MipDataPacket
        data_point: mscl.MipDataPoint

        # This is a tight loop that fetches data from the IMU constantly. It looks ugly and written
        # the way as it is for performance reasons. Some of the optimizations implemented include
        # - using no functions inside the loop (this is typically 2x faster per packet)
        # - if-elif statements instead of a `match` / `setattr` / `hasattr` (2x-5x faster / packet)
        # - using 2 inner loops depending on the type of packet, this reduces the number of `if`
        # checks the interpreter has to do
        # - Using integers for comparison instead of strings (O(1) vs O(n) complexity)
        # - Checking for raw data packets or estimated data packets, not both
        # - Using msgspec to serialize and deserialize the packets, which is faster than pickle
        # - High priority for the process
        while self.is_running:
            # Retrieve data packets from the IMU.
            packets: mscl.MipDataPackets = node.getDataPackets(timeout=10)

            self._imu_packets_per_cycle.value = len(packets)

            messages = []
            for packet in packets:
                # Extract the timestamp from the packet.
                timestamp = packet.collectedTimestamp().nanoseconds()
                descriptor_set = packet.descriptorSet()

                # Initialize packet with the timestamp, determines if the packet is raw or estimated
                if descriptor_set == RAW_DESCRIPTOR_SET:
                    imu_data_packet = RawDataPacket(timestamp)
                    # Iterate through each data point in the packet.
                    for data_point in packet.data():
                        # Extract the channel name of the data point.
                        qualifier = data_point.qualifier()
                        field_name = data_point.field()

                        if field_name == SCALED_ACCEL_FIELD:
                            # Scaled acceleration data
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.scaledAccelX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.scaledAccelY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.scaledAccelZ = data_point.as_float()

                        elif field_name == SCALED_GYRO_FIELD:
                            # Scaled gyroscope data
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.scaledGyroX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.scaledGyroY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.scaledGyroZ = data_point.as_float()

                        elif field_name == DELTA_VEL_FIELD:
                            # Delta velocity (change in velocity)
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.deltaVelX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.deltaVelY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.deltaVelZ = data_point.as_float()

                        elif field_name == DELTA_THETA_FIELD:
                            # Delta theta (change in orientation)
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.deltaThetaX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.deltaThetaY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.deltaThetaZ = data_point.as_float()

                        elif (
                            field_name == SCALED_AMBIENT_PRESSURE_FIELD
                            and qualifier == AMBIENT_PRESSURE_QUALIFIER
                        ):
                            # Scaled ambient pressure data
                            imu_data_packet.scaledAmbientPressure = data_point.as_float()

                elif descriptor_set == ESTIMATED_DESCRIPTOR_SET:
                    imu_data_packet = EstimatedDataPacket(timestamp)
                    for data_point in packet.data():
                        # Extract the channel name of the data point.
                        qualifier = data_point.qualifier()
                        field_name = data_point.field()

                        if (
                            field_name == EST_PRESSURE_ALT_FIELD
                            and qualifier == PRESSURE_ALT_QUALIFIER
                        ):
                            # Estimated pressure altitude
                            imu_data_packet.estPressureAlt = data_point.as_float()

                        elif (
                            field_name == EST_ORIENT_QUATERNION_FIELD
                            and qualifier == ATTITUDE_UNCERT_QUALIFIER
                        ):
                            # Estimated orientation quaternion
                            matrix = data_point.as_Matrix()
                            # The imu sends the quaternions as a matrix, so we have to unpack it
                            imu_data_packet.estOrientQuaternionW = matrix.as_floatAt(0, 0)
                            imu_data_packet.estOrientQuaternionX = matrix.as_floatAt(0, 1)
                            imu_data_packet.estOrientQuaternionY = matrix.as_floatAt(0, 2)
                            imu_data_packet.estOrientQuaternionZ = matrix.as_floatAt(0, 3)

                        elif (
                            field_name == EST_ATTITUDE_UNCERT_FIELD
                            and qualifier == ATTITUDE_UNCERT_QUALIFIER
                        ):
                            # Estimated attitude uncertainty quaternion
                            matrix = data_point.as_Matrix()
                            imu_data_packet.estAttitudeUncertQuaternionW = matrix.as_floatAt(0, 0)
                            imu_data_packet.estAttitudeUncertQuaternionX = matrix.as_floatAt(0, 1)
                            imu_data_packet.estAttitudeUncertQuaternionY = matrix.as_floatAt(0, 2)
                            imu_data_packet.estAttitudeUncertQuaternionZ = matrix.as_floatAt(0, 3)

                        elif field_name == EST_ANGULAR_RATE_FIELD:
                            # Estimated angular rate
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.estAngularRateX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.estAngularRateY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.estAngularRateZ = data_point.as_float()

                        elif field_name == EST_COMPENSATED_ACCEL_FIELD:
                            # Estimated compensated acceleration
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.estCompensatedAccelX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.estCompensatedAccelY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.estCompensatedAccelZ = data_point.as_float()

                        elif field_name == EST_LINEAR_ACCEL_FIELD:
                            # Estimated linear acceleration
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.estLinearAccelX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.estLinearAccelY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.estLinearAccelZ = data_point.as_float()

                        elif field_name == EST_GRAVITY_VECTOR_FIELD:
                            # Estimated gravity vector
                            if qualifier == X_QUALIFIER:
                                imu_data_packet.estGravityVectorX = data_point.as_float()
                            elif qualifier == Y_QUALIFIER:
                                imu_data_packet.estGravityVectorY = data_point.as_float()
                            elif qualifier == Z_QUALIFIER:
                                imu_data_packet.estGravityVectorZ = data_point.as_float()

                        # Check if the data point is invalid and update the invalid fields list.
                        if not data_point.valid():
                            if imu_data_packet.invalid_fields is None:
                                imu_data_packet.invalid_fields = []
                            imu_data_packet.invalid_fields.append(data_point.channelName())  # ty: ignore[possibly-unbound-attribute]
                else:
                    continue  # We never actually reach here, but keeping it just in case

                    # Unused channels include: `gpsCorrelTimestamp(Tow,WeekNum,Flags)`,
                    # `estFilterGpsTimeTow`, `estFilterGpsTimeWeekNum`. But we
                    # can't exclude it from the IMU settings cause it says it's not recommended
                    #     print(field_name, data_point.channelName())

                messages.append(imu_data_packet)

            self._queued_imu_packets.put_many(messages)

    def _query_imu_for_data_packets(self, port: str) -> None:
        """
        The loop that fetches data from the IMU.

        It runs in parallel with the main loop.
        :param port: the port that the IMU is connected to
        """
        with contextlib.suppress(KeyboardInterrupt):
            self._fetch_data_loop(port)
