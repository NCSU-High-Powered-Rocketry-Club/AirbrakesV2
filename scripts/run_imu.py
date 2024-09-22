"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.test_imu`
For the pi, you will have to use python3
"""

from constants import FREQUENCY, PORT, TEST_LOGS_PATH
from airbrakes.hardware.imu import IMU
from airbrakes.data_handling.logger import Logger


imu = IMU(PORT, FREQUENCY)
logger = Logger(TEST_LOGS_PATH)

try:
    imu.start()
    logger.start()
    while True:
        print(imu.get_imu_data_packet())
except KeyboardInterrupt:  # Stop running IMU and logger if the user presses Ctrl+C
    pass
finally:
    imu.stop()
    logger.stop()
