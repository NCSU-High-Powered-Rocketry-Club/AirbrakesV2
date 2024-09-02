import time
from Airbrakes.imu import IMUDataPacket
from Airbrakes.logger import Logger

def main():
    logger = Logger(["state", "extension", "acceleration_x", "acceleration_y", "acceleration_z", "gyro_x", "gyro_y", "gyro_z"])

    for _ in range(10):
        logger.log("state", 0.0, IMUDataPacket(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        time.sleep(0.1)
    logger.stop()

if __name__ == "__main__":
    main()
