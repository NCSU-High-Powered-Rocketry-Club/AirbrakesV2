"""Module for interacting with the IMU (Inertial measurement unit) on the rocket."""

import collections
import contextlib
import multiprocessing

# Try to import the MSCL library, if it fails, warn the user, this is necessary because installing
# mscl is annoying and we really just have it installed on the pi
with contextlib.suppress(ImportError):
    import mscl
    # We should print a warning, but that messes with how the sim display looks

from airbrakes.data_handling.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)
from constants import ESTIMATED_DESCRIPTOR_SET, MAX_QUEUE_SIZE, RAW_DESCRIPTOR_SET


class IMU:
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

    __slots__ = (
        "_data_fetch_process",
        "_data_queue",
        "_running",
    )

    def __init__(self, port: str, frequency: int) -> None:
        """
        Initializes the object that interacts with the physical IMU connected to the pi.
        :param port: the port that the IMU is connected to
        :param frequency: the frequency that the IMU is set to poll at (this can be checked in
            SensorConnect)
        """
        # Shared Queue which contains the latest data from the IMU. The MAX_QUEUE_SIZE is there
        # to prevent memory issues. Realistically, the queue size never exceeds 50 packets when
        # it's being logged.
        self._data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue(
            MAX_QUEUE_SIZE
        )
        # Makes a boolean value that is shared between processes
        self._running = multiprocessing.Value("b", False)
        # Starts the process that fetches data from the IMU
        self._data_fetch_process = multiprocessing.Process(
            target=self._query_imu_for_data_packets, args=(port, frequency), name="IMU Process"
        )

    @property
    def is_running(self) -> bool:
        """
        Returns whether the process fetching data from the IMU is running.
        :return: True if the process is running, False otherwise
        """
        return self._running.value

    def start(self) -> None:
        """
        Starts the process separate from the main process for fetching data from the IMU.
        """
        self._running.value = True
        self._data_fetch_process.start()

    def stop(self) -> None:
        """
        Stops the process separate from the main process for fetching data from the IMU.
        """
        self._running.value = False
        # Fetch all packets which are not yet fetched and discard them, so main() does not get
        # stuck (i.e. deadlocks) waiting for the process to finish. A more technical explanation:
        # Case 1: .put() is blocking and if the queue is full, it keeps waiting for the queue to
        # be empty, and thus the process never .joins().
        # Case 2: The other process finishes up before we call the below method, so there might be
        # nothing in the queue, and then calling get_imu_data_packet() will block the main process
        # indefinitely (that's why there's a timeout in the get_imu_data_packet() method).
        with contextlib.suppress(multiprocessing.TimeoutError):
            self.get_imu_data_packets()

        with contextlib.suppress(multiprocessing.TimeoutError):
            self._data_fetch_process.join(timeout=2)

    def get_imu_data_packet(self) -> IMUDataPacket | None:
        """
        Gets the last available data packet from the IMU.
        Note: If `get_imu_data_packet` is called slower than the frequency set, the data will not
        be the latest, but the first in the queue.
        :return: an IMUDataPacket object containing the latest data from the IMU. If a value is not
            available, it will be None.
        """
        return self._data_queue.get(timeout=3)

    def get_imu_data_packets(self) -> collections.deque[IMUDataPacket]:
        """
        Returns all available data packets from the IMU.
        :return: A deque containing the specified number of data packets
        """
        # We use a deque because it's faster than a list for popping from the left
        data_packets = collections.deque()
        # While there is data in the queue, get the data packet and add it to the dequeue which we
        # return
        while not self._data_queue.empty():
            data_packets.append(self.get_imu_data_packet())

        return data_packets

    def _query_imu_for_data_packets(self, port: str, frequency: int) -> None:
        """
        The loop that fetches data from the IMU. It runs in parallel with the main loop.
        :param port: the port that the IMU is connected to
        :param frequency: the frequency that the IMU is set to poll at
        """
        with contextlib.suppress(KeyboardInterrupt):
            self._fetch_data_loop(port, frequency)

    def _fetch_data_loop(self, port: str, frequency: int) -> None:
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
                    channel: str = data_point.channelName()
                    # This cpp file was the only place I was able to find all the channel names
                    # https://github.com/LORD-MicroStrain/MSCL/blob/master/MSCL/source/mscl/MicroStrain/MIP/MipTypes.cpp
                    # Check if the channel name is one we want to save
                    if hasattr(imu_data_packet, channel) or "Quaternion" in channel:
                        # First checks if the data point needs special handling, if not, just set
                        # the attribute
                        match channel:
                            # These specific data points are matrix's rather than doubles
                            case "estAttitudeUncertQuaternion" | "estOrientQuaternion":
                                # This makes a 4x1 matrix from the data point with the data as
                                # [[w], [x], [y], [z]]
                                matrix = data_point.as_Matrix()
                                # Sets the W, X, Y, and Z of the quaternion to the data packet
                                setattr(imu_data_packet, f"{channel}W", matrix.as_floatAt(0, 0))
                                setattr(imu_data_packet, f"{channel}X", matrix.as_floatAt(0, 1))
                                setattr(imu_data_packet, f"{channel}Y", matrix.as_floatAt(0, 2))
                                setattr(imu_data_packet, f"{channel}Z", matrix.as_floatAt(0, 3))
                            case _:
                                # Because the attribute names in our data packet classes are the
                                # same as the channel names, we can just set the attribute to the
                                # value of the data point.
                                setattr(imu_data_packet, channel, data_point.as_float())

                        # If the data point is invalid, add it to the invalid fields list:
                        if not data_point.valid():
                            if imu_data_packet.invalid_fields is None:
                                imu_data_packet.invalid_fields = []
                            imu_data_packet.invalid_fields.append(channel)

                # Put the latest data into the shared queue
                self._data_queue.put(imu_data_packet)
