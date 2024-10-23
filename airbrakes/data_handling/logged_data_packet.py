"""Module for describing the data packet for the logger to log"""

import msgspec

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket


class LoggedDataPacket(msgspec.Struct):
    """
    Represents a collection of all data that the logger can log in a line. Not every field will be filled in every
    packet. While maybe not the sleekest solution, it is very easy to implement, and allows us to see exactly what data
    we are logging.
    """

    state: str
    extension: float

    # IMU Data Packet Fields
    timestamp: float
    invalid_fields: list[str] | None = None

    # Raw Data Packet Fields
    scaledAccelX: float | None = None
    scaledAccelY: float | None = None
    scaledAccelZ: float | None = None
    scaledGyroX: float | None = None
    scaledGyroY: float | None = None
    scaledGyroZ: float | None = None
    deltaVelX: float | None = None
    deltaVelY: float | None = None
    deltaVelZ: float | None = None
    deltaThetaX: float | None = None
    deltaThetaY: float | None = None
    deltaThetaZ: float | None = None

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
    estGravityVectorX: float | None = None
    estGravityVectorY: float | None = None
    estGravityVectorZ: float | None = None

    # Processed Data Packet Fields
    current_altitude: float | None = None
    vertical_velocity: float | None = None
    # Not logging maxes because they are easily found

    def set_imu_data_packet_attributes(self, imu_data_packet: IMUDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the IMU data packet. Rounds the
        float values to 8 decimal places, if the value is a float.

        This function could be a lot cleaner and just use getattr() and setattr(), but that is
        slower and takes up 15% of the main loop execution time.

        :param imu_data_packet: The IMU data packet to set the attributes from.
        """
        if isinstance(imu_data_packet, EstimatedDataPacket):
            # super ugly code, but it results in a 10-14% speedup overall
            # The speed improvements come from not looping through the fields of the data packet
            # and using getattr() and setattr() to set the attributes of the logged data packet.
            # Additionally, rounding using f-strings is faster than round() by about ~25%
            if imu_data_packet.estOrientQuaternionW is not None:
                self.estOrientQuaternionW = f"{imu_data_packet.estOrientQuaternionW:.8f}"
            if imu_data_packet.estOrientQuaternionX is not None:
                self.estOrientQuaternionX = f"{imu_data_packet.estOrientQuaternionX:.8f}"
            if imu_data_packet.estOrientQuaternionY is not None:
                self.estOrientQuaternionY = f"{imu_data_packet.estOrientQuaternionY:.8f}"
            if imu_data_packet.estOrientQuaternionZ is not None:
                self.estOrientQuaternionZ = f"{imu_data_packet.estOrientQuaternionZ:.8f}"
            if imu_data_packet.estAttitudeUncertQuaternionW is not None:
                self.estAttitudeUncertQuaternionW = f"{imu_data_packet.estAttitudeUncertQuaternionW:.8f}"
            if imu_data_packet.estAttitudeUncertQuaternionX is not None:
                self.estAttitudeUncertQuaternionX = f"{imu_data_packet.estAttitudeUncertQuaternionX:.8f}"
            if imu_data_packet.estAttitudeUncertQuaternionY is not None:
                self.estAttitudeUncertQuaternionY = f"{imu_data_packet.estAttitudeUncertQuaternionY:.8f}"
            if imu_data_packet.estAttitudeUncertQuaternionZ is not None:
                self.estAttitudeUncertQuaternionZ = f"{imu_data_packet.estAttitudeUncertQuaternionZ:.8f}"
            if imu_data_packet.estAngularRateX is not None:
                self.estAngularRateX = f"{imu_data_packet.estAngularRateX:.8f}"
            if imu_data_packet.estAngularRateY is not None:
                self.estAngularRateY = f"{imu_data_packet.estAngularRateY:.8f}"
            if imu_data_packet.estAngularRateZ is not None:
                self.estAngularRateZ = f"{imu_data_packet.estAngularRateZ:.8f}"
            if imu_data_packet.estCompensatedAccelX is not None:
                self.estCompensatedAccelX = f"{imu_data_packet.estCompensatedAccelX:.8f}"
            if imu_data_packet.estCompensatedAccelY is not None:
                self.estCompensatedAccelY = f"{imu_data_packet.estCompensatedAccelY:.8f}"
            if imu_data_packet.estCompensatedAccelZ is not None:
                self.estCompensatedAccelZ = f"{imu_data_packet.estCompensatedAccelZ:.8f}"
            if imu_data_packet.estLinearAccelX is not None:
                self.estLinearAccelX = f"{imu_data_packet.estLinearAccelX:.8f}"
            if imu_data_packet.estLinearAccelY is not None:
                self.estLinearAccelY = f"{imu_data_packet.estLinearAccelY:.8f}"
            if imu_data_packet.estLinearAccelZ is not None:
                self.estLinearAccelZ = f"{imu_data_packet.estLinearAccelZ:.8f}"
            if imu_data_packet.estGravityVectorX is not None:
                self.estGravityVectorX = f"{imu_data_packet.estGravityVectorX:.8f}"
            if imu_data_packet.estGravityVectorY is not None:
                self.estGravityVectorY = f"{imu_data_packet.estGravityVectorY:.8f}"
            if imu_data_packet.estGravityVectorZ is not None:
                self.estGravityVectorZ = f"{imu_data_packet.estGravityVectorZ:.8f}"
            if imu_data_packet.estPressureAlt is not None:
                self.estPressureAlt = f"{imu_data_packet.estPressureAlt:.8f}"

        else:
            if imu_data_packet.scaledAccelX is not None:
                self.scaledAccelX = f"{imu_data_packet.scaledAccelX:.8f}"
            if imu_data_packet.scaledAccelY is not None:
                self.scaledAccelY = f"{imu_data_packet.scaledAccelY:.8f}"
            if imu_data_packet.scaledAccelZ is not None:
                self.scaledAccelZ = f"{imu_data_packet.scaledAccelZ:.8f}"
            if imu_data_packet.scaledGyroX is not None:
                self.scaledGyroX = f"{imu_data_packet.scaledGyroX:.8f}"
            if imu_data_packet.scaledGyroY is not None:
                self.scaledGyroY = f"{imu_data_packet.scaledGyroY:.8f}"
            if imu_data_packet.scaledGyroZ is not None:
                self.scaledGyroZ = f"{imu_data_packet.scaledGyroZ:.8f}"
            if imu_data_packet.deltaVelX is not None:
                self.deltaVelX = f"{imu_data_packet.deltaVelX:.8f}"
            if imu_data_packet.deltaVelY is not None:
                self.deltaVelY = f"{imu_data_packet.deltaVelY:.8f}"
            if imu_data_packet.deltaVelZ is not None:
                self.deltaVelZ = f"{imu_data_packet.deltaVelZ:.8f}"
            if imu_data_packet.deltaThetaX is not None:
                self.deltaThetaX = f"{imu_data_packet.deltaThetaX:.8f}"
            if imu_data_packet.deltaThetaY is not None:
                self.deltaThetaY = f"{imu_data_packet.deltaThetaY:.8f}"
            if imu_data_packet.deltaThetaZ is not None:
                self.deltaThetaZ = f"{imu_data_packet.deltaThetaZ:.8f}"

        # Common field between the two
        self.invalid_fields = imu_data_packet.invalid_fields

    def set_processed_data_packet_attributes(self, processed_data_packet: ProcessedDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the processed data packet.
        """
        self.current_altitude = processed_data_packet.current_altitude
        self.vertical_velocity = processed_data_packet.vertical_velocity
