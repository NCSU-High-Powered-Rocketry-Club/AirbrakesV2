"""Module for interacting with the IMU (Inertial measurement unit) on the rocket."""

import collections
import multiprocessing

import mscl

from airbrakes.constants import ESTIMATED_DESCRIPTOR_SET, RAW_DESCRIPTOR_SET
from airbrakes.imu.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket


class IMU:
    """
    Represents the IMU on the rocket. It's used to get the current acceleration of the rocket. This is used to interact
    with the data collected by the Parker-LORD 3DMCX5-AR.

    It uses multiprocessing rather than threading to truly run in parallel with the main loop. We're doing this is
    because the IMU constantly polls data and can be slow, so it's better to run it in parallel.

    Here is the setup docs: https://github.com/LORD-MicroStrain/MSCL/blob/master/HowToUseMSCL.md
    """

    __slots__ = (
        "_data_fetch_process",
        "_data_queue",
        "_running",
    )

    def __init__(self, port: str, frequency: int, upside_down: bool):
        # Shared Queue which contains the latest data from the IMU
        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue()
        self._running = multiprocessing.Value("b", False)  # Makes a boolean value that is shared between processes

        # Starts the process that fetches data from the IMU
        self._data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop, args=(port, frequency, upside_down)
        )

    @property
    def is_running(self) -> bool:
        """
        Returns whether the process fetching data from the IMU is running.
        """
        return self._running.value

    def start(self):
        """
        Starts the process fetching data from the IMU.
        """
        self._running.value = True
        self._data_fetch_process.start()

    def _fetch_data_loop(self, port: str, frequency: int, _: bool):
        """
        This is the loop that fetches data from the IMU. It runs in parallel with the main loop.
        """
        # Connect to the IMU
        connection = mscl.Connection.Serial(port)
        node = mscl.InertialNode(connection)
        timeout = int(1000 / frequency)

        while self._running.value:
            # Get the latest data packets from the IMU, with the help of `getDataPackets`.
            # `getDataPackets` accepts a timeout in milliseconds.
            # During IMU configuration (outside of this code), we set the sampling rate of the IMU
            # as 1ms for RawDataPackets, and 2ms for EstimatedDataPackets.
            # So we use a timeout of 1000 / frequency = 10ms which should be more
            # than enough. If the timeout is hit, the function will return an empty list.

            packets: mscl.MipDataPackets = node.getDataPackets(timeout)
            # Every loop iteration we get the latest data in form of packets from the imu
            for packet in packets:
                # The data packet from the IMU:
                packet: mscl.MipDataPacket

                # Get the timestamp of the packet
                timestamp = packet.collectedTimestamp().nanoseconds()

                # Initialize packet with the timestamp, determines if the packet is raw or estimated
                if packet.descriptorSet() == ESTIMATED_DESCRIPTOR_SET:
                    imu_data_packet = EstimatedDataPacket(timestamp)
                elif packet.descriptorSet() == RAW_DESCRIPTOR_SET:
                    imu_data_packet = RawDataPacket(timestamp)
                else:
                    # This is an unknown packet, so we skip it
                    continue

                # Each of these packets has multiple data points
                for data_point in packet.data():
                    data_point: mscl.MipDataPoint
                    if data_point.valid():
                        channel = data_point.channelName()
                        # This cpp file was the only place I was able to find all the channel names
                        # https://github.com/LORD-MicroStrain/MSCL/blob/master/MSCL/source/mscl/MicroStrain/MIP/MipTypes.cpp
                        # Makes a dictionary of attributes to set on the imu_data_packet
                        data_to_set = {}

                        # Special handling for quaternions
                        if channel in ("estAttitudeUncertQuaternion", "estOrientQuaternion"):
                            matrix = data_point.as_Matrix()
                            quaternion_tuple = tuple(matrix[i, 0] for i in range(matrix.rows()))
                            data_to_set.update({
                                f"{channel}X": quaternion_tuple[0],
                                f"{channel}Y": quaternion_tuple[1],
                                f"{channel}Z": quaternion_tuple[2],
                                f"{channel}W": quaternion_tuple[3],
                            })
                        else:
                            # General case, add the attribute to the dictionary
                            data_to_set[channel] = data_point.as_float()

                        # Update the attributes of the imu_data_packet in one call, this is much faster than setting
                        # each attribute individually
                        imu_data_packet.__dict__.update(data_to_set)

                # Put the latest data into the shared queue
                self._data_queue.put(imu_data_packet)

    def get_imu_data_packet(self) -> IMUDataPacket:
        """
        Gets the last available data packet from the IMU.

        Note: If `get_imu_data_packet` is called slower than the frequency set, the data will not
        be the latest, but the first in the queue.

        :return: an IMUDataPacket object containing the latest data from the IMU. If a value is
            not available, it will be None.
        """
        return self._data_queue.get()

    def get_imu_data_packets(self) -> collections.deque[IMUDataPacket]:
        """Returns all available data packets from the IMU.

        :return: A deque containing the specified number of data packets
        """

        data_packets = collections.deque()

        while not self._data_queue.empty():
            data_packet = self.get_imu_data_packet()
            data_packets.append(data_packet)

        return data_packets

    def stop(self):
        """
        Stops the process fetching data from the IMU. This should be called when the program is shutting down.
        """
        self._running.value = False
        # Waits for the process to finish before stopping it
        self._data_fetch_process.join()
