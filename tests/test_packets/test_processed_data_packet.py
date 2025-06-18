import pytest

from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket


@pytest.fixture
def processor_data_packet():
    return ProcessorDataPacket(
        current_altitude=TestProcessorDataPacket.current_altitude,
        vertical_velocity=TestProcessorDataPacket.vertical_velocity,
        vertical_acceleration=TestProcessorDataPacket.vertical_acceleration,
        time_since_last_data_packet=TestProcessorDataPacket.time_since_last_data_packet,
    )


class TestProcessorDataPacket:
    """
    Tests for the ProcessorDataPacket class.
    """

    current_altitude = 0.0
    vertical_velocity = 0.0
    vertical_acceleration = 0.0
    time_since_last_data_packet = 1

    def test_init(self, processor_data_packet):
        packet = processor_data_packet
        assert packet.current_altitude == self.current_altitude
        assert packet.vertical_velocity == self.vertical_velocity
        assert packet.vertical_acceleration == self.vertical_acceleration
        assert packet.time_since_last_data_packet == self.time_since_last_data_packet

    def test_required_args(self):
        with pytest.raises(TypeError):
            ProcessorDataPacket()
