import pytest

from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket


@pytest.fixture
def processor_data_packet():
    return ProcessorDataPacket(
        current_altitude=TestProcessorDataPacket.current_altitude,
        vertical_velocity=TestProcessorDataPacket.vertical_velocity,
    )


class TestProcessorDataPacket:
    """
    Tests for the ProcessorDataPacket class.
    """

    current_altitude = 0.0
    vertical_velocity = 0.0

    def test_init(self, processor_data_packet):
        packet = processor_data_packet
        assert packet.current_altitude == self.current_altitude
        assert packet.vertical_velocity == self.vertical_velocity

    def test_required_args(self):
        with pytest.raises(TypeError):
            ProcessorDataPacket()