"""
Make sure you are in the root directory of the project, not inside Scripts, and run the following command:
`python -m Scripts.test_imu`
For the pi, you will have to use python3
"""
from Airbrakes.imu import IMU

imu = IMU()

while True:
    print(imu.get_imu_data())
