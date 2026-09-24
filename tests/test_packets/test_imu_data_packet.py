"""Tests for typed raw and estimated IMU packet schemas."""

import msgspec

from airbrakes.data_handling.packets.imu_data_packet import (
    EstimatedDataPacket,
    IMUDataPacket,
    RawDataPacket,
)


def test_raw_packet_preserves_source_fields_and_optional_values():
    packet = RawDataPacket(
        timestamp=123,
        invalid_fields="scaledGyro",
        scaledAccelX=1.0,
        scaledGyroZ=2.0,
        deltaVelY=3.0,
        deltaThetaZ=4.0,
        scaledAmbientPressure=5.0,
    )

    assert isinstance(packet, IMUDataPacket)
    assert packet.timestamp == 123
    assert packet.invalid_fields == "scaledGyro"
    assert packet.scaledAccelX == 1.0
    assert packet.scaledGyroZ == 2.0
    assert packet.deltaVelY == 3.0
    assert packet.deltaThetaZ == 4.0
    assert packet.scaledAmbientPressure == 5.0
    assert packet.scaledAccelY is None


def test_estimated_packet_round_trips_through_msgspec_with_its_tag():
    packet = EstimatedDataPacket(
        timestamp=456,
        estPressureAlt=100.0,
        estOrientQuaternionW=1.0,
        estAngularRateY=2.0,
        estCompensatedAccelZ=3.0,
        estGravityVectorX=4.0,
    )

    decoded = msgspec.msgpack.decode(
        msgspec.msgpack.encode(packet), type=RawDataPacket | EstimatedDataPacket
    )

    assert isinstance(decoded, EstimatedDataPacket)
    assert decoded == packet
    assert decoded.estLinearAccelX is None
