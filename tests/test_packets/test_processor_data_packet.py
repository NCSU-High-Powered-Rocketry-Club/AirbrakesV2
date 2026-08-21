import pytest

from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket


@pytest.fixture
def processor_data_packet():
    return ProcessorDataPacket(
        current_altitude=TestProcessorDataPacket.current_altitude,
        vertical_velocity_meters_per_s=TestProcessorDataPacket.vertical_velocity_meters_per_s,
        horizontal_velocity_meters_per_s=TestProcessorDataPacket.horizontal_velocity_meters_per_s,
        tilt_angle_degrees=TestProcessorDataPacket.tilt_angle_degrees,
        angular_rate_deg_per_s=TestProcessorDataPacket.angular_rate_deg_per_s,
        timestamp_seconds=TestProcessorDataPacket.timestamp_seconds,
    )


class TestProcessorDataPacket:
    """
    Tests for the ProcessorDataPacket class.
    """

    current_altitude = 0.0
    vertical_velocity_meters_per_s = 0.0
    horizontal_velocity_meters_per_s = 0.0
    tilt_angle_degrees = 0.0
    angular_rate_deg_per_s = 0.0
    timestamp_seconds = 0.0

    def test_init(self, processor_data_packet):
        packet = processor_data_packet
        assert packet.current_altitude == self.current_altitude
        assert packet.vertical_velocity_meters_per_s == self.vertical_velocity_meters_per_s
        assert packet.horizontal_velocity_meters_per_s == self.horizontal_velocity_meters_per_s
        assert packet.tilt_angle_degrees == self.tilt_angle_degrees
        assert packet.angular_rate_deg_per_s == self.angular_rate_deg_per_s
        assert packet.timestamp_seconds == self.timestamp_seconds

    def test_required_args(self):
        with pytest.raises(TypeError):
            ProcessorDataPacket()
