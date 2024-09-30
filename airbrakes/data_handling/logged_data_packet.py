"""Module for describing the data packet for the logger to log"""

import msgspec

from airbrakes.data_handling.imu_data_packet import IMUDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import DATA_PACKET_DECIMAL_PLACES


class LoggedDataPacket(msgspec.Struct):
    """
    Represents a collection of all data that the logger can log in a line. Not every field will be filled in every
    packet. While maybe not the sleekest solution, it is very easy to implement, and allows us to see exactly what data
    we are logging.
    """

    state: str
    extension: float
    timestamp: float

    # Raw Data Packet Fields
    scaledAccelX: float | None = None
    scaledAccelY: float | None = None
    scaledAccelZ: float | None = None
    scaledGyroX: float | None = None
    scaledGyroY: float | None = None
    scaledGyroZ: float | None = None

    # Estimated Data Packet Fields
    estOrientQuaternionW: float | None = None
    estOrientQuaternionX: float | None = None
    estOrientQuaternionY: float | None = None
    estOrientQuaternionZ: float | None = None
    estPressureAlt: float | None = None
    estAttitudeUncertQuaternionW: float | None = None
    estAttitudeUncertQuaternionX: float | None = None
    estAttitudeUncertQuaternionY: float | None = None
    estAttitudeUncertQuaternionZ: float | None = None
    estAngularRateX: float | None = None
    estAngularRateY: float | None = None
    estAngularRateZ: float | None = None
    estCompensatedAccelX: float | None = None
    estCompensatedAccelY: float | None = None
    estCompensatedAccelZ: float | None = None
    estLinearAccelX: float | None = None
    estLinearAccelY: float | None = None
    estLinearAccelZ: float | None = None

    # Processed Data Packet Fields
    avg_acceleration: tuple[float, float, float] | None = None
    current_altitude: float | None = None
    speed: float | None = None
    # Not logging maxes because they are easily found

    def set_imu_data_packet_attributes(self, imu_data_packet: IMUDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the IMU data packet.
        """
        for key in imu_data_packet.__struct_fields__:
            if hasattr(self, key):
                value = getattr(imu_data_packet, key)
                # Only logs the 8 decimal places as there is already so much noise in the data
                if isinstance(value, float):
                    value = round(value, DATA_PACKET_DECIMAL_PLACES)
                setattr(self, key, value)
            else:
                raise AttributeError(f"{key} is not a valid attribute")

    def set_processed_data_packet_attributes(self, processed_data_packet: ProcessedDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the processed data packet.
        """
        self.avg_acceleration = processed_data_packet.avg_acceleration
        self.current_altitude = processed_data_packet.current_altitude
        self.speed = processed_data_packet.speed
