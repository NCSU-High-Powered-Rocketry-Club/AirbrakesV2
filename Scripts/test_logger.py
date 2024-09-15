import time
from collections import deque

from airbrakes.imu.imu_data_packet import RawDataPacket  # Assuming this is your IMU data packet class
from airbrakes.logger import Logger


def main():
    # Initialize the logger
    logger = Logger()

    # Log for 5 seconds
    start_time = time.time()
    while time.time() - start_time < 5:
        # Create fake IMU data
        imu_data_list = deque([RawDataPacket(int(time.time()), 1, 2, 3, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)])
        logger.log("TEST_STATE", 0.5, imu_data_list)

    # Stop the logger after 5 seconds
    logger.stop()


if __name__ == "__main__":
    main()
