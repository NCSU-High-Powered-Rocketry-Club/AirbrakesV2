"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.run_imu`
For the pi, you will have to use python3
"""

from constants import IMUSettings,LoggerSettings
from airbrakes.hardware.imu import IMU
from airbrakes.data_handling.logger import Logger


imu = IMU(IMUSettings.PORT.value, IMUSettings.FREQUENCY.value)
logger = Logger(LoggerSettings.TEST_LOGS_PATH.value)

try:
    imu.start()
    logger.start()
    while True:
        imu.get_imu_data_packet()
except KeyboardInterrupt:  # Stop running IMU and logger if the user presses Ctrl+C
    pass
finally:
    imu.stop()
    logger.stop()
