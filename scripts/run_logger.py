"""Module for testing how the logger module runs."""

import time
from collections import deque

from firm_client import FIRMDataPacket

from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.constants import TEST_LOGS_PATH
from airbrakes.data_handling.logger import Logger


def main():
    # Initialize the logger
    logger = Logger(TEST_LOGS_PATH)
    data_processor = DataProcessor()

    # Log for 5 seconds, and automatically stops logging
    start_time = time.time()
    try:
        logger.start()
        while time.time() - start_time < 5:
            # Create fake FIRM data
            packet = FIRMDataPacket.default_zero()
            packet.timestamp_seconds = time.time()
            firm_data_list = deque(FIRMDataPacket.default_zero())
            logger.log("TEST_STATE", 0.5, firm_data_list, data_processor)
    except KeyboardInterrupt:  # Stop logging if the user presses Ctrl+C
        pass
    finally:
        logger.stop()


if __name__ == "__main__":
    main()
