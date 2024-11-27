"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.run_imu`
For the pi, you will have to use python3
"""

from constants import PORT
from airbrakes.hardware.imu import IMU


imu = IMU(PORT)

try:
    imu.start()
    while True:
        print(imu.get_imu_data_packet())
except KeyboardInterrupt:  # Stop running IMU if the user presses Ctrl+C
    pass
finally:
    imu.stop()
