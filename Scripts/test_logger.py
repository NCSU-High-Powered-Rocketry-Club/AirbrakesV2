import time
from Airbrakes.imu import IMUDataPacket
from Airbrakes.logger import Logger


CSV_HEADERS = ["state", "extension"] + list(IMUDataPacket(0.0).__slots__)


def main():
    logger = Logger(CSV_HEADERS)

    for _ in range(10):
        logger.log("state", 0.0, IMUDataPacket(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        time.sleep(0.1)
    logger.stop()


if __name__ == "__main__":
    main()
