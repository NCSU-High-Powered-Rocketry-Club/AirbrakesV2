import time
from Airbrakes.imu import IMUDataPacket
from Airbrakes.logger import Logger

def main():
    logger = Logger(["state", "extension", "acceleration_x", "acceleration_y", "acceleration_z", "gyro_x", "gyro_y", "gyro_z"])

    try:
        # Simulate logging in a loop
        for _ in range(10):
            print("cdjsaji")
            logger.log("state", 0.0, IMUDataPacket(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
            time.sleep(1)  # Sleep to simulate time between logs
    except KeyboardInterrupt:
        pass
    finally:
        logger.stop()  # Ensure the logging process is stopped properly

if __name__ == "__main__":
    main()
