"""Module for describing the data packet for the logger to log"""

import msgspec

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, RawDataPacket
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
    scaledAccelX: str | None = None
    scaledAccelY: str | None = None
    scaledAccelZ: str | None = None
    scaledGyroX: str | None = None
    scaledGyroY: str | None = None
    scaledGyroZ: str | None = None
    deltaVelX: str | None = None
    deltaVelY: str | None = None
    deltaVelZ: str | None = None
    deltaThetaX: str | None = None
    deltaThetaY: str | None = None
    deltaThetaZ: str | None = None

    # Estimated Data Packet Fields
    estOrientQuaternionW: str | None = None
    estOrientQuaternionX: str | None = None
    estOrientQuaternionY: str | None = None
    estOrientQuaternionZ: str | None = None
    estPressureAlt: str | None = None
    estAttitudeUncertQuaternionW: str | None = None
    estAttitudeUncertQuaternionX: str | None = None
    estAttitudeUncertQuaternionY: str | None = None
    estAttitudeUncertQuaternionZ: str | None = None
    estAngularRateX: str | None = None
    estAngularRateY: str | None = None
    estAngularRateZ: str | None = None
    estCompensatedAccelX: str | None = None
    estCompensatedAccelY: str | None = None
    estCompensatedAccelZ: str | None = None
    estLinearAccelX: str | None = None
    estLinearAccelY: str | None = None
    estLinearAccelZ: str | None = None
    estGravityVectorX: str | None = None
    estGravityVectorY: str | None = None
    estGravityVectorZ: str | None = None

    # Processed Data Packet Fields
    current_altitude: str | None = None
    vertical_velocity: str | None = None
    vertical_acceleration: str | None = None

    # field which is not in any of the data packets:
    predicted_apogee: str | None = None

    def set_estimated_data_packet_attributes(self, data_packet: EstimatedDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the estimated data packet. Rounds the
        float values to 8 decimal places, if the value is a float.

        This function could be a lot cleaner and just use getattr() and setattr(), but that is
        slower and takes up 15% of the main loop execution time.

        :param estimated_data_packet: The estimated data packet to set the attributes from.
        """
        # super ugly code, but it results in a 10-14% speedup overall
        # The speed improvements come from not looping through the fields of the data packet
        # and using getattr() and setattr() to set the attributes of the logged data packet.
        # Additionally, rounding using f-strings is faster than round() by about ~25%
        if data_packet.estOrientQuaternionW is not None:
            self.estOrientQuaternionW = f"{data_packet.estOrientQuaternionW:.8f}"
        if data_packet.estOrientQuaternionX is not None:
            self.estOrientQuaternionX = f"{data_packet.estOrientQuaternionX:.8f}"
        if data_packet.estOrientQuaternionY is not None:
            self.estOrientQuaternionY = f"{data_packet.estOrientQuaternionY:.8f}"
        if data_packet.estOrientQuaternionZ is not None:
            self.estOrientQuaternionZ = f"{data_packet.estOrientQuaternionZ:.8f}"
        if data_packet.estAttitudeUncertQuaternionW is not None:
            self.estAttitudeUncertQuaternionW = f"{data_packet.estAttitudeUncertQuaternionW:.8f}"
        if data_packet.estAttitudeUncertQuaternionX is not None:
            self.estAttitudeUncertQuaternionX = f"{data_packet.estAttitudeUncertQuaternionX:.8f}"
        if data_packet.estAttitudeUncertQuaternionY is not None:
            self.estAttitudeUncertQuaternionY = f"{data_packet.estAttitudeUncertQuaternionY:.8f}"
        if data_packet.estAttitudeUncertQuaternionZ is not None:
            self.estAttitudeUncertQuaternionZ = f"{data_packet.estAttitudeUncertQuaternionZ:.8f}"
        if data_packet.estAngularRateX is not None:
            self.estAngularRateX = f"{data_packet.estAngularRateX:.8f}"
        if data_packet.estAngularRateY is not None:
            self.estAngularRateY = f"{data_packet.estAngularRateY:.8f}"
        if data_packet.estAngularRateZ is not None:
            self.estAngularRateZ = f"{data_packet.estAngularRateZ:.8f}"
        if data_packet.estCompensatedAccelX is not None:
            self.estCompensatedAccelX = f"{data_packet.estCompensatedAccelX:.8f}"
        if data_packet.estCompensatedAccelY is not None:
            self.estCompensatedAccelY = f"{data_packet.estCompensatedAccelY:.8f}"
        if data_packet.estCompensatedAccelZ is not None:
            self.estCompensatedAccelZ = f"{data_packet.estCompensatedAccelZ:.8f}"
        if data_packet.estLinearAccelX is not None:
            self.estLinearAccelX = f"{data_packet.estLinearAccelX:.8f}"
        if data_packet.estLinearAccelY is not None:
            self.estLinearAccelY = f"{data_packet.estLinearAccelY:.8f}"
        if data_packet.estLinearAccelZ is not None:
            self.estLinearAccelZ = f"{data_packet.estLinearAccelZ:.8f}"
        if data_packet.estGravityVectorX is not None:
            self.estGravityVectorX = f"{data_packet.estGravityVectorX:.8f}"
        if data_packet.estGravityVectorY is not None:
            self.estGravityVectorY = f"{data_packet.estGravityVectorY:.8f}"
        if data_packet.estGravityVectorZ is not None:
            self.estGravityVectorZ = f"{data_packet.estGravityVectorZ:.8f}"
        if data_packet.estPressureAlt is not None:
            self.estPressureAlt = f"{data_packet.estPressureAlt:.8f}"

    def set_raw_data_packet_attributes(self, data_packet: RawDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the raw data packet. Rounds the
        float values to 8 decimal places, if the value is a float.
        :param data_packet: The raw data packet to set the attributes from.
        """
        if data_packet.scaledAccelX is not None:
            self.scaledAccelX = f"{data_packet.scaledAccelX:.8f}"
        if data_packet.scaledAccelY is not None:
            self.scaledAccelY = f"{data_packet.scaledAccelY:.8f}"
        if data_packet.scaledAccelZ is not None:
            self.scaledAccelZ = f"{data_packet.scaledAccelZ:.8f}"
        if data_packet.scaledGyroX is not None:
            self.scaledGyroX = f"{data_packet.scaledGyroX:.8f}"
        if data_packet.scaledGyroY is not None:
            self.scaledGyroY = f"{data_packet.scaledGyroY:.8f}"
        if data_packet.scaledGyroZ is not None:
            self.scaledGyroZ = f"{data_packet.scaledGyroZ:.8f}"
        if data_packet.deltaVelX is not None:
            self.deltaVelX = f"{data_packet.deltaVelX:.8f}"
        if data_packet.deltaVelY is not None:
            self.deltaVelY = f"{data_packet.deltaVelY:.8f}"
        if data_packet.deltaVelZ is not None:
            self.deltaVelZ = f"{data_packet.deltaVelZ:.8f}"
        if data_packet.deltaThetaX is not None:
            self.deltaThetaX = f"{data_packet.deltaThetaX:.8f}"
        if data_packet.deltaThetaY is not None:
            self.deltaThetaY = f"{data_packet.deltaThetaY:.8f}"
        if data_packet.deltaThetaZ is not None:
            self.deltaThetaZ = f"{data_packet.deltaThetaZ:.8f}"

    def set_processed_data_packet_attributes(self, processed_data_packet: ProcessedDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the processed data packet.
        """
        self.current_altitude = f"{processed_data_packet.current_altitude:.8f}"
        self.vertical_velocity = f"{processed_data_packet.vertical_velocity:.8f}"
        self.vertical_acceleration = f"{processed_data_packet.vertical_acceleration:.8f}"
