"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.test_imu`
For the pi, you will have to use python3
"""

from airbrakes.constants import FREQUENCY, PORT, UPSIDE_DOWN
from airbrakes.imu.imu import IMU
from airbrakes.logger import Logger
from pathlib import Path

from airbrakes.imu.imu_data_packet import EstimatedDataPacket, RawDataPacket


imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)
logger = Logger(Path("test_logs/"))

with imu, logger:
    while True:
        print(imu.get_imu_data_packet())
