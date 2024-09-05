import multiprocessing
import mscl


class IMUDataPacket:
    """
    Represents a collection of data packets from the IMU. It contains the acceleration, velocity, altitude, yaw, pitch,
    roll of the rocket and the timestamp of the data.
    """

    __slots__ = (
        "timestamp",
        "acceleration",
        "velocity",
        "altitude",
        "yaw",
        "pitch",
        "roll",
    )

    def __init__(
        self,
        timestamp: float,
        acceleration: float = None,
        velocity: float = None,
        altitude: float = None,
        yaw: float = None,
        pitch: float = None,
        roll: float = None,
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

    __slots__ = (
        "port",
        "frequency",
        "upside_down",
        "connection",
        "node",
        "latest_data",
        "running",
        "data_fetch_process",
    )

    def __init__(self, port: str, frequency: int, upside_down: bool):
        self.port = port
        self.frequency = frequency
        self.upside_down = upside_down

        # Connect to the IMU
        self.connection = mscl.Connection.Serial(self.port)
        self.node = mscl.InertialNode(self.connection)

        # Shared dictionary to store the most recent data packet
        self.latest_data = multiprocessing.Manager().dict()
        self.running = multiprocessing.Value("b", True)  # Makes a boolean value that is shared between processes

        # Starts the process that fetches data from the IMU
        self.data_fetch_process = multiprocessing.Process(target=self._fetch_data_loop)
        self.data_fetch_process.start()

    def _fetch_data_loop(self):
        """
        This is the loop that fetches data from the IMU. It runs in parallel with the main loop.
        """
        while self.running.value:
            # Get the latest data packets from the IMU with a timeout of 10ms
            packets = self.node.getDataPackets(1000.0 / self.frequency)
            for packet in packets:
                # TODO: Add a check to see if the packet is new -- make a list or dictionary of timestamps for each packet
                # TODO: See which packets contain what data
                timestamp = packet.collectedTimestamp().nanoseconds()
                for data_point in packet.data():
                    if data_point.valid():
                        channel = data_point.channelName()
                        # This cpp file was the only place I was able to find all the channel names
                        # https://github.com/LORD-MicroStrain/MSCL/blob/master/MSCL/source/mscl/MicroStrain/MIP/MipTypes.cpp
                        match channel:
                            case "estLinearAccelX":
                                accel = data_point.as_float()
                                if self.upside_down:
                                    accel = -accel
                                self.latest_data["accel"] = accel
                            case "estLinearVelX":
                                velocity = data_point.as_float()
                                if self.upside_down:
                                    velocity = -velocity
                                self.latest_data["velocity"] = velocity
                            case "estPressureAlt":
                                self.latest_data["altitude"] = data_point.as_float()
                            # TODO: Check the units and if their orientations are correct
                            case "estYaw":
                                self.latest_data["yaw"] = data_point.as_float()
                            case "estPitch":
                                self.latest_data["pitch"] = data_point.as_float()
                            case "estRoll":
                                self.latest_data["roll"] = data_point.as_float()

                # Update the timestamp after processing all data points
                self.latest_data["timestamp"] = timestamp

    def get_imu_data(self) -> IMUDataPacket:
        """
        Gets the latest data from the IMU.
        :return: an IMUDataPacket object containing the latest data from the IMU. If a value is not available, it will
        be None.
        """
        # Create an IMUDataPacket object using the latest data
        return IMUDataPacket(
            # When you use .get() on a dictionary, it will return None if the key doesn't exist
            timestamp=self.latest_data.get("timestamp", 0.0),
            acceleration=self.latest_data.get("acceleration"),
            velocity=self.latest_data.get("velocity"),
            altitude=self.latest_data.get("altitude"),
            yaw=self.latest_data.get("yaw"),
            pitch=self.latest_data.get("pitch"),
            roll=self.latest_data.get("roll"),
        )

    def stop(self):
        """
        Stops the process fetching data from the IMU. This should be called when the program is shutting down.
        """
        self.running.value = False
        # Waits for the process to finish before stopping it
        self.data_fetch_process.join()
