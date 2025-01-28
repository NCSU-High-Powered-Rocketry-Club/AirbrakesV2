"""Module for interacting with the IMU (Inertial measurement unit) on the rocket."""

import contextlib
import multiprocessing
import sys

# Try to import the MSCL library, if it fails, warn the user. mscl does not work on Windows with
# Python 3.13.
with contextlib.suppress(ImportError):
    from python_mscl import mscl

# We should print a warning, but that messes with how the replay display looks

# If we are not on windows, we can use the faster_fifo library to speed up the queue operations
if sys.platform != "win32":
    from faster_fifo import Queue
else:
    pass

from airbrakes.constants import (
    BUFFER_SIZE_IN_BYTES,
    ESTIMATED_DESCRIPTOR_SET,
    MAX_QUEUE_SIZE,
    RAW_DESCRIPTOR_SET,
)
from airbrakes.hardware.base_imu import BaseIMU
from airbrakes.telemetry.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)


class IMU(BaseIMU):
    """
    Represents the IMU on the rocket. It's used to get the current acceleration of the rocket.
    This is used to interact with the data collected by the Parker-LORD 3DMCX5-AR.
    (https://www.microstrain.com/inertial-sensors/3dm-cx5-15).

    It uses multiprocessing rather than threading to truly run in parallel with the main loop.
    We're doing this is because the IMU constantly polls data and can be slow, so it's better to
    run it in parallel.

    Here is the setup docs: https://github.com/LORD-MicroStrain/MSCL/blob/master/HowToUseMSCL.md
    Here is the software for configuring the IMU: https://www.microstrain.com/software/sensorconnect
    """

    def __init__(self, port: str) -> None:
        """
        Initializes the object that interacts with the physical IMU connected to the pi.
        :param port: the port that the IMU is connected to
        """
        # Shared Queue which contains the latest data from the IMU. The MAX_QUEUE_SIZE is there
        # to prevent memory issues. Realistically, the queue size never exceeds 50 packets when
        # it's being logged.
        # We will never run the actual IMU on Windows, so we can use the faster_fifo library always:
        _data_queue: Queue[IMUDataPacket] = Queue(
            maxsize=MAX_QUEUE_SIZE, max_size_bytes=BUFFER_SIZE_IN_BYTES
        )
        # Starts the process that fetches data from the IMU
        data_fetch_process = multiprocessing.Process(
            target=self._query_imu_for_data_packets, args=(port,), name="IMU Process"
        )
        super().__init__(data_fetch_process, _data_queue)

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE PROCESS -------------------------
    @staticmethod
    def _initialize_packet(packet: "mscl.MipDataPacket") -> IMUDataPacket | None:
        """
        Initialize an IMU data packet based on its descriptor set.
        :param packet: The data packet from the IMU.
        :return: An IMUDataPacket, or None if the packet is unrecognized.
        """
        # Extract the timestamp from the packet.
        timestamp = packet.collectedTimestamp().nanoseconds()

        # Initialize packet with the timestamp, determines if the packet is raw or estimated
        if packet.descriptorSet() == ESTIMATED_DESCRIPTOR_SET:
            return EstimatedDataPacket(timestamp)
        if packet.descriptorSet() == RAW_DESCRIPTOR_SET:
            return RawDataPacket(timestamp)
        return None

    @staticmethod
    def _process_data_point(
        data_point: "mscl.MipDataPoint", channel: str, imu_data_packet: IMUDataPacket
    ) -> None:
        """
        Process an individual data point and set its value in the data packet object. Modifies
        `imu_data_packet` in place.
        :param data_point: The IMU data point containing the measurement.
        :param channel: The channel name of the data point.
        :param imu_data_packet: The data packet object to update.
        """
        # Handle special channels that represent quaternion data.
        if channel in {"estAttitudeUncertQuaternion", "estOrientQuaternion"}:
            # Convert quaternion data into a 4x1 matrix and set its components.
            matrix = data_point.as_Matrix()
            setattr(imu_data_packet, f"{channel}W", matrix.as_floatAt(0, 0))
            setattr(imu_data_packet, f"{channel}X", matrix.as_floatAt(0, 1))
            setattr(imu_data_packet, f"{channel}Y", matrix.as_floatAt(0, 2))
            setattr(imu_data_packet, f"{channel}Z", matrix.as_floatAt(0, 3))
        else:
            # Set other data points directly as attributes in the data packet.
            setattr(imu_data_packet, channel, data_point.as_float())

        # Check if the data point is invalid and update the invalid fields list.
        if not data_point.valid():
            if imu_data_packet.invalid_fields is None:
                imu_data_packet.invalid_fields = []
            imu_data_packet.invalid_fields.append(channel)

    @staticmethod
    def _process_packet_data(packet: "mscl.MipDataPacket", imu_data_packet: IMUDataPacket) -> None:
        """
        Process the data points in the packet and update the data packet object. Modifies
        `imu_data_packet` in place.
        :param packet: The IMU data packet containing multiple data points.
        :param imu_data_packet: The initialized data packet object to populate.
        """
        # Iterate through each data point in the packet.
        data_point: mscl.MipDataPoint
        for data_point in packet.data():
            # Extract the channel name of the data point.
            channel = data_point.channelName()

            # Check if the channel is relevant for the data packet, we check for quaternions
            # separately because the IMU sends them over as a matrix, but we store each of them
            # individually as fields.
            if hasattr(imu_data_packet, channel) or "Quaternion" in channel:
                # Process and set the data point value in the data packet.
                IMU._process_data_point(data_point, channel, imu_data_packet)

    def _fetch_data_loop(self, port: str) -> None:
        """
        Continuously fetch data packets from the IMU and process them.
        :param port: The serial port to connect to the IMU.
        """
        # Connect to the IMU and initialize the node used for getting data packets
        connection = mscl.Connection.Serial(port)
        node = mscl.InertialNode(connection)
        while self.is_running:
            # Retrieve data packets from the IMU.
            packets: mscl.MipDataPackets = node.getDataPackets(timeout=10)
            print(len(packets))
            packet: mscl.MipDataPacket
            for packet in packets:
                # Extract the timestamp from the packet.
                timestamp = packet.collectedTimestamp().nanoseconds()

                # Initialize packet with the timestamp, determines if the packet is raw or estimated
                if packet.descriptorSet() == ESTIMATED_DESCRIPTOR_SET:
                    imu_data_packet = EstimatedDataPacket(timestamp)
                elif packet.descriptorSet() == RAW_DESCRIPTOR_SET:
                    imu_data_packet = RawDataPacket(timestamp)
                else:
                    continue

                # Iterate through each data point in the packet.
                data_point: mscl.MipDataPoint
                for data_point in packet.data():
                    # print(data_point.field())
                    # Extract the channel name of the data point.
                    # channel = data_point.channelName()


                    # print("!", channel, data_point.field(), data_point.qualifier())
                    match data_point.field(), data_point.qualifier():
                        case 32775, 1:
                            imu_data_packet.deltaThetaX = data_point.as_float()
                        case 32775, 2:
                            imu_data_packet.deltaThetaY = data_point.as_float()
                        case 32775, 3:
                            imu_data_packet.deltaThetaZ = data_point.as_float()
                        case 32776, 1:
                            imu_data_packet.deltaVelX = data_point.as_float()
                        case 32776, 2:
                            imu_data_packet.deltaVelY = data_point.as_float()
                        case 32776, 3:
                            imu_data_packet.deltaVelZ = data_point.as_float()
                        case 33294, 1:
                            imu_data_packet.estAngularRateX = data_point.as_float()
                        case 33294, 2:
                            imu_data_packet.estAngularRateY = data_point.as_float()
                        case 33294, 3:
                            imu_data_packet.estAngularRateZ = data_point.as_float()
                        case 33298, 5:
                            matrix = data_point.as_Matrix()
                            imu_data_packet.estAttitudeUncertQuaternionW = matrix.as_floatAt(0,0)
                            imu_data_packet.estAttitudeUncertQuaternionX = matrix.as_floatAt(0,1)
                            imu_data_packet.estAttitudeUncertQuaternionY = matrix.as_floatAt(0,2)
                            imu_data_packet.estAttitudeUncertQuaternionZ = matrix.as_floatAt(0,3)
                        case 33308, 1:
                            imu_data_packet.estCompensatedAccelX = data_point.as_float()
                        case 33308, 2:
                            imu_data_packet.estCompensatedAccelY = data_point.as_float()
                        case 33308, 3:
                            imu_data_packet.estCompensatedAccelZ = data_point.as_float()
                        case 33299, 1:
                            imu_data_packet.estGravityVectorX = data_point.as_float()
                        case 33299, 2:
                            imu_data_packet.estGravityVectorY = data_point.as_float()
                        case 33299, 3:
                            imu_data_packet.estGravityVectorZ = data_point.as_float()
                        case 33293, 1:
                            imu_data_packet.estLinearAccelX = data_point.as_float()
                        case 33293, 2:
                            imu_data_packet.estLinearAccelY = data_point.as_float()
                        case 33293, 3:
                            imu_data_packet.estLinearAccelZ = data_point.as_float()
                        case 33283, 5:
                            matrix = data_point.as_Matrix()
                            imu_data_packet.estOrientQuaternionW = matrix.as_floatAt(0,0)
                            imu_data_packet.estOrientQuaternionX = matrix.as_floatAt(0,1)
                            imu_data_packet.estOrientQuaternionY = matrix.as_floatAt(0,2)
                            imu_data_packet.estOrientQuaternionZ = matrix.as_floatAt(0,3)
                        case 33313, 67:
                            imu_data_packet.estPressureAlt = data_point.as_float()
                        case 32772, 1:
                            imu_data_packet.scaledAccelX = data_point.as_float()
                        case 32772, 2:
                            imu_data_packet.scaledAccelY = data_point.as_float()
                        case 32772, 3:
                            imu_data_packet.scaledAccelZ = data_point.as_float()
                        case 32791, 58:
                            imu_data_packet.scaledAmbientPressure = data_point.as_float()
                        case 32773, 1:
                            imu_data_packet.scaledGyroX = data_point.as_float()
                        case 32773, 2:
                            imu_data_packet.scaledGyroY = data_point.as_float()
                        case 32773, 3:
                            imu_data_packet.scaledGyroZ = data_point.as_float()
                    
                    # Check if the data point is invalid and update the invalid fields list.
                    if not data_point.valid():
                        if imu_data_packet.invalid_fields is None:
                            imu_data_packet.invalid_fields = []
                        # TODO
                        imu_data_packet.invalid_fields.append(channel)
                self._data_queue.put(imu_data_packet)


    def _query_imu_for_data_packets(self, port: str) -> None:
        """
        The loop that fetches data from the IMU. It runs in parallel with the main loop.
        :param port: the port that the IMU is connected to
        """
        with contextlib.suppress(KeyboardInterrupt):
            self._fetch_data_loop(port)
