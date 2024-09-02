"""
Make sure you are in the root directory of the project, not inside Scripts, and run the following command:
`python -m Scripts.test_imu`
For the pi, you will have to use python3
"""
from Airbrakes.imu import IMU

# Should be checked before launch
UPSIDE_DOWN = True
# The port that the IMU is connected to
PORT = "/dev/ttyACM0"
# The frequency in which the IMU polls data in Hz
FREQUENCY = 100

imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)

while True:
    print(imu.get_imu_data())
