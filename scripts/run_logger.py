"""
Module for testing how the logger module runs.
"""

import time
from collections import deque

from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.constants import TEST_LOGS_PATH
from airbrakes.telemetry.packets.imu_data_packet import RawDataPacket
from airbrakes.telemetry.logger import Logger


def main():
    # Initialize the logger
    logger = Logger(TEST_LOGS_PATH)
    data_processor = DataProcessor()

    # Log for 5 seconds, and automatically stops logging
    start_time = time.time()
    try:
        logger.start()
        while time.time() - start_time < 5:
            # Create fake IMU data
            imu_data_list = deque([RawDataPacket(int(time.time()), 1, 2, 3, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)])
            logger.log("TEST_STATE", 0.5, imu_data_list, data_processor)
    except KeyboardInterrupt:  # Stop logging if the user presses Ctrl+C
        pass
    finally:
        logger.stop()


if __name__ == "__main__":
    main()
