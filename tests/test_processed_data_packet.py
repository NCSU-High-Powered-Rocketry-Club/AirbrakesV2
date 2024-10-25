import pytest

from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket


@pytest.fixture
def processed_data_packet():
    return ProcessedDataPacket(
        current_altitude=TestProcessedDataPacket.current_altitude,
        vertical_velocity=TestProcessedDataPacket.velocity,
    )


class TestProcessedDataPacket:
    """Tests for the ProcessedDataPacket class."""

    current_altitude = 0.0
    vertical_velocity = 0.0

    def test_init(self, processed_data_packet):
        packet = processed_data_packet
        assert packet.current_altitude == self.current_altitude
        assert packet.velocity == self.vertical_velocity

    def test_required_args(self):
        with pytest.raises(TypeError):
            ProcessedDataPacket()
