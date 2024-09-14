"""Module to test the logger module."""

from airbrakes.imu.imu_data_packet import IMUDataPacket
from airbrakes.logger import Logger


def main():
    logger = Logger()

    while True:  # TODO: will not work
        logger.log("state", 0.0, IMUDataPacket(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))


if __name__ == "__main__":
    main()
