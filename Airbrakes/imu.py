import multiprocessing
import mscl


class IMUDataPacket:
    """
    Represents a data packet from the IMU. It contains the acceleration, velocity, altitude, and timestamp of the data
    """

    def __init__(self, timestamp: float, accel: float = None, velocity: float = None, altitude: float = None):
        self.timestamp = timestamp
        self.accel = accel
        self.velocity = velocity
        self.altitude = altitude


class IMU:
    """
    Represents the IMU on the rocket. It's used to get the current acceleration of the rocket. This is used to interact
    with the data collected by the Parker-LORD 3DMCX5-AR.

    It uses multiprocessing rather than threading to truly run in parallel with the main loop. We're doing this is
    because the IMU constantly polls data and can be slow, so it's better to run it in parallel.

    Here is the setup docs: https://github.com/LORD-MicroStrain/MSCL/blob/master/HowToUseMSCL.md
    """

    # Should be checked before launch
    UPSIDE_DOWN = True
    # The port that the IMU is connected to
    PORT = "/dev/ttyACM0"
    # The frequency in which the IMU polls data in Hz
    FREQUENCY = 100

    def __init__(self):
        # Connect to the IMU
        self.connection = mscl.Connection.Serial(self.PORT)
        self.node = mscl.InertialNode(self.connection)

        # Shared dictionary to store the most recent data packet
        self.latest_data = multiprocessing.Manager().dict()
        self.running = multiprocessing.Value('b', True)  # Makes a boolean value that is shared between processes

        # Starts the process that fetches data from the IMU
        self.data_fetch_process = multiprocessing.Process(target=self._fetch_data_loop)
        self.data_fetch_process.start()

    # TODO: Make sure you fully understand the manager code and make a data point class

    def _fetch_data_loop(self):
        while self.running.value:
            packets = self.node.getDataPackets(1000.0 / self.FREQUENCY)
            for packet in packets:
                for data_point in packet.data():
                    if data_point.valid():
                        # Store the latest valid data point in the dictionary
                        self.latest_data['accel'] = data_point.as_float()
                        self.latest_data['timestamp'] = packet.collectedTimestamp().nanoseconds()

    def get_imu_data(self):
        # Convert the shared dictionary to a regular dictionary before returning
        return dict(self.latest_data)

    def stop(self):
        self.running.value = False
        # Waits for the process to finish before stopping it
        self.data_fetch_process.join()
