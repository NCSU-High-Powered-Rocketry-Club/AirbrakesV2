"""Module for describing the data packet for the logger to log"""

import msgspec

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket
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
    avg_acceleration: tuple[float, float, float] | None = None
    current_altitude: float | None = None
    speed: float | None = None
    # Not logging maxes because they are easily found

    def set_imu_data_packet_attributes(self, imu_data_packet: IMUDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the IMU data packet. Rounds the
        float values to 8 decimal places, if the value is a float.

        This function could be a lot cleaner and just use getattr() and setattr(), but that is
        slower and takes up 15% of the main loop execution time.

        :param ldp: The logged data packet to set the attributes of.
        :param imu_data_packet: The IMU data packet to set the attributes from.
        """
        idp = imu_data_packet
        if isinstance(idp, EstimatedDataPacket):
            # super ugly code, but it results in a 10-14% speedup overall
            # The speed improvements come from not looping through the fields of the data packet
            # and using getattr() and setattr() to set the attributes of the logged data packet.
            # Additionally, rounding using f-strings is faster than round() by about ~25%
            if idp.estOrientQuaternionW is not None:
                self.estOrientQuaternionW = f"{idp.estOrientQuaternionW:.8f}"
            if idp.estOrientQuaternionX is not None:
                self.estOrientQuaternionX = f"{idp.estOrientQuaternionX:.8f}"
            if idp.estOrientQuaternionY is not None:
                self.estOrientQuaternionY = f"{idp.estOrientQuaternionY:.8f}"
            if idp.estOrientQuaternionZ is not None:
                self.estOrientQuaternionZ = f"{idp.estOrientQuaternionZ:.8f}"
            if idp.estAttitudeUncertQuaternionW is not None:
                self.estAttitudeUncertQuaternionW = f"{idp.estAttitudeUncertQuaternionW:.8f}"
            if idp.estAttitudeUncertQuaternionX is not None:
                self.estAttitudeUncertQuaternionX = f"{idp.estAttitudeUncertQuaternionX:.8f}"
            if idp.estAttitudeUncertQuaternionY is not None:
                self.estAttitudeUncertQuaternionY = f"{idp.estAttitudeUncertQuaternionY:.8f}"
            if idp.estAttitudeUncertQuaternionZ is not None:
                self.estAttitudeUncertQuaternionZ = f"{idp.estAttitudeUncertQuaternionZ:.8f}"
            if idp.estAngularRateX is not None:
                self.estAngularRateX = f"{idp.estAngularRateX:.8f}"
            if idp.estAngularRateY is not None:
                self.estAngularRateY = f"{idp.estAngularRateY:.8f}"
            if idp.estAngularRateZ is not None:
                self.estAngularRateZ = f"{idp.estAngularRateZ:.8f}"
            if idp.estCompensatedAccelX is not None:
                self.estCompensatedAccelX = f"{idp.estCompensatedAccelX:.8f}"
            if idp.estCompensatedAccelY is not None:
                self.estCompensatedAccelY = f"{idp.estCompensatedAccelY:.8f}"
            if idp.estCompensatedAccelZ is not None:
                self.estCompensatedAccelZ = f"{idp.estCompensatedAccelZ:.8f}"
            if idp.estLinearAccelX is not None:
                self.estLinearAccelX = f"{idp.estLinearAccelX:.8f}"
            if idp.estLinearAccelY is not None:
                self.estLinearAccelY = f"{idp.estLinearAccelY:.8f}"
            if idp.estLinearAccelZ is not None:
                self.estLinearAccelZ = f"{idp.estLinearAccelZ:.8f}"
            if idp.estGravityVectorX is not None:
                self.estGravityVectorX = f"{idp.estGravityVectorX:.8f}"
            if idp.estGravityVectorY is not None:
                self.estGravityVectorY = f"{idp.estGravityVectorY:.8f}"
            if idp.estGravityVectorZ is not None:
                self.estGravityVectorZ = f"{idp.estGravityVectorZ:.8f}"
            if idp.estPressureAlt is not None:
                self.estPressureAlt = f"{idp.estPressureAlt:.8f}"

        if isinstance(idp, RawDataPacket):
            if idp.scaledAccelX is not None:
                self.scaledAccelX = f"{idp.scaledAccelX:.8f}"
            if idp.scaledAccelY is not None:
                self.scaledAccelY = f"{idp.scaledAccelY:.8f}"
            if idp.scaledAccelZ is not None:
                self.scaledAccelZ = f"{idp.scaledAccelZ:.8f}"
            if idp.scaledGyroX is not None:
                self.scaledGyroX = f"{idp.scaledGyroX:.8f}"
            if idp.scaledGyroY is not None:
                self.scaledGyroY = f"{idp.scaledGyroY:.8f}"
            if idp.scaledGyroZ is not None:
                self.scaledGyroZ = f"{idp.scaledGyroZ:.8f}"
            if idp.deltaVelX is not None:
                self.deltaVelX = f"{idp.deltaVelX:.8f}"
            if idp.deltaVelY is not None:
                self.deltaVelY = f"{idp.deltaVelY:.8f}"
            if idp.deltaVelZ is not None:
                self.deltaVelZ = f"{idp.deltaVelZ:.8f}"
            if idp.deltaThetaX is not None:
                self.deltaThetaX = f"{idp.deltaThetaX:.8f}"
            if idp.deltaThetaY is not None:
                self.deltaThetaY = f"{idp.deltaThetaY:.8f}"
            if idp.deltaThetaZ is not None:
                self.deltaThetaZ = f"{idp.deltaThetaZ:.8f}"

        # Common field between the two
        self.invalid_fields = idp.invalid_fields

    def set_processed_data_packet_attributes(self, processed_data_packet: ProcessedDataPacket) -> None:
        """
        Sets the attributes of the data packet corresponding to the processed data packet.
        """
        self.avg_acceleration = processed_data_packet.avg_acceleration
        self.current_altitude = processed_data_packet.current_altitude
        self.speed = processed_data_packet.speed
