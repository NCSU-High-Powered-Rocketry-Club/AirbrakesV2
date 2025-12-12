import pytest

from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket


@pytest.fixture
def processor_data_packet():
    return ProcessorDataPacket(
        current_altitude=TestProcessorDataPacket.current_altitude,
        vertical_velocity=TestProcessorDataPacket.vertical_velocity,
        vertical_acceleration=TestProcessorDataPacket.vertical_acceleration,
        time_since_last_data_packet=TestProcessorDataPacket.time_since_last_data_packet,
        velocity_magnitude=TestProcessorDataPacket.velocity_magnitude,
        current_pitch_degrees=TestProcessorDataPacket.current_pitch_degrees,
    )


class TestProcessorDataPacket:
    """
    Tests for the ProcessorDataPacket class.
    """

    current_altitude = 0.0
    velocity_magnitude = 0.0
    vertical_velocity = 0.0
    vertical_acceleration = 0.0
    current_pitch_degrees = 0.0
    time_since_last_data_packet = 1

    def test_init(self, processor_data_packet):
        packet = processor_data_packet
        assert packet.current_altitude == self.current_altitude
        assert packet.vertical_velocity == self.vertical_velocity
        assert packet.velocity_magnitude == self.velocity_magnitude
        assert packet.vertical_acceleration == self.vertical_acceleration
        assert packet.time_since_last_data_packet == self.time_since_last_data_packet
        assert packet.current_pitch_degrees == self.current_pitch_degrees

    def test_required_args(self):
        with pytest.raises(TypeError):
            ProcessorDataPacket()
