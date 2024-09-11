"""Module for interacting with the IMU (Inertial measurement unit) on the rocket."""

import multiprocessing

import mscl


class IMUDataPacket:
    """
    Represents a collection of data packets from the IMU. It contains the acceleration, velocity, altitude, yaw, pitch,
    roll of the rocket and the timestamp of the data.
    """

    __slots__ = (
        "acceleration",
        "altitude",
        "pitch",
        "roll",
        "timestamp",
        "velocity",
        "yaw",
    )

    def __init__(
        self,
        timestamp: float,
        acceleration: float | None = None,
        velocity: float | None = None,
        altitude: float | None = None,
        yaw: float | None = None,
        pitch: float | None = None,
        roll: float | None = None,
    ):
        self.timestamp = timestamp
        self.acceleration = acceleration
        self.velocity = velocity
        self.altitude = altitude
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll

    def __str__(self):
        return (
            f"IMUDataPacket(timestamp={self.timestamp}, acceleration={self.acceleration}, "
            f"velocity={self.velocity}, altitude={self.altitude}, yaw={self.yaw}, pitch={self.pitch}, "
            f"roll={self.roll})"
        )


class IMU:
    """
    Represents the IMU on the rocket. It's used to get the current acceleration of the rocket. This is used to interact
    with the data collected by the Parker-LORD 3DMCX5-AR.

    It uses multiprocessing rather than threading to truly run in parallel with the main loop. We're doing this is
    because the IMU constantly polls data and can be slow, so it's better to run it in parallel.

    Here is the setup docs: https://github.com/LORD-MicroStrain/MSCL/blob/master/HowToUseMSCL.md
    """

    ESTIMATED_DESCRIPTOR_SET = 130
    RAW_DESCRIPTOR_SET = 128

    __slots__ = (
        "connection",
        "data_fetch_process",
        "data_queue",
        "running",
    )

    def __init__(self, port: str, frequency: int, upside_down: bool):
        # Shared Queue which contains the latest data from the IMU
        self.data_queue: multiprocessing.Queue[IMUDataPacket] = multiprocessing.Queue()
        self.running = multiprocessing.Value("b", True)  # Makes a boolean value that is shared between processes

        # Starts the process that fetches data from the IMU
        self.data_fetch_process = multiprocessing.Process(
            target=self._fetch_data_loop, args=(port, frequency, upside_down)
        )
        self.data_fetch_process.start()

    def _fetch_data_loop(self, port: str, frequency: int, _: bool):
        """
        This is the loop that fetches data from the IMU. It runs in parallel with the main loop.
        """
        # Connect to the IMU
        connection = mscl.Connection.Serial(port)
        node = mscl.InertialNode(connection)
        timeout = int(1000 / frequency)

        while self.running.value:
            # Get the latest data packets from the IMU, with the help of `getDataPackets`.
            # `getDataPackets` accepts a timeout in milliseconds.
            # Testing has shown that the maximum rate at which we can fetch data is roughly every
            # 2ms on average, so we use a timeout of = 1000 / frequency = 10ms which should be more
            # than enough.
            # (help needed: what happens if the timeout is hit? An empty list? Exception?)
            packets: mscl.MipDataPackets = node.getDataPackets(timeout)
            # Every loop iteration we get the latest data in form of packets from the imu
            for packet in packets:
                # The data packet from the IMU:
                packet: mscl.MipDataPacket
                timestamp = packet.collectedTimestamp().nanoseconds()

                # The data points we need specifically, collected in a class.
                imu_data_packet = IMUDataPacket(timestamp)  # initialize packet with the timestamp

                # Each of these packets has multiple data points
                for data_point in packet.data():
                    data_point: mscl.MipDataPoint
                    if data_point.valid():
                        channel = data_point.channelName()
                        # This cpp file was the only place I was able to find all the channel names
                        # https://github.com/LORD-MicroStrain/MSCL/blob/master/MSCL/source/mscl/MicroStrain/MIP/MipTypes.cpp
                        if packet.descriptorSet() == self.ESTIMATED_DESCRIPTOR_SET:
                            match channel:
                                case "estPressureAlt":
                                    imu_data_packet.altitude = data_point.as_float()
                                # TODO: Check the units and if their orientations are correct
                                case "estYaw":
                                    imu_data_packet.yaw = data_point.as_float()
                                case "estPitch":
                                    imu_data_packet.pitch = data_point.as_float()
                                case "estRoll":
                                    imu_data_packet.roll = data_point.as_float()
                        elif packet.descriptorSet() == self.RAW_DESCRIPTOR_SET:
                            # depending on the descriptor set, its a different type of packet
                            pass

                # Put the latest data into the shared queue
                self.data_queue.put(imu_data_packet)

    def get_imu_data(self) -> IMUDataPacket:
        """
        Gets the latest data from the IMU.

        Note: If `get_imu_data` is called slower than the frequency set, the data will not be the
        latest, but the first in the queue.

        :return: an IMUDataPacket object containing the latest data from the IMU. If a value is
        not available, it will be None.
        """
        return self.data_queue.get()

    def stop(self):
        """
        Stops the process fetching data from the IMU. This should be called when the program is shutting down.
        """
        self.running.value = False
        # Waits for the process to finish before stopping it
        self.data_fetch_process.join()
