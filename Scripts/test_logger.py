"""Module to test the logger module."""

from airbrakes.imu import IMUDataPacket
from airbrakes.logger import Logger

CSV_HEADERS = ["state", "extension", *list(IMUDataPacket(0.0).__slots__)]


def main():
    logger = Logger(CSV_HEADERS)

    while True:
        logger.log("state", 0.0, IMUDataPacket(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    main()
