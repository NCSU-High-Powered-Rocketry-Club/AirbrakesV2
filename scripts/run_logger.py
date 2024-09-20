"""Module for testing how the logger module runs."""

import time
from collections import deque

from airbrakes.constants import LOGS_PATH
from airbrakes.imu.imu_data_packet import RawDataPacket
from airbrakes.logger import Logger


def main():
    # Initialize the logger
    logger = Logger(LOGS_PATH)

    # Log for 5 seconds, and automatically stops logging
    start_time = time.time()
    try:
        logger.start()
        while time.time() - start_time < 5:
            # Create fake IMU data
            imu_data_list = deque([RawDataPacket(int(time.time()), 1, 2, 3, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)])
            logger.log("TEST_STATE", 0.5, imu_data_list)
    except KeyboardInterrupt:  # Stop logging if the user presses Ctrl+C
        pass
    finally:
        logger.stop()


if __name__ == "__main__":
    main()
