import pytest

from airbrakes.data_handling.packets.processed_data_packet import ProcessedDataPacket


@pytest.fixture
def processed_data_packet():
    return ProcessedDataPacket(
        current_altitude=TestProcessedDataPacket.current_altitude,
        vertical_velocity=TestProcessedDataPacket.vertical_velocity,
        vertical_acceleration=TestProcessedDataPacket.vertical_acceleration,
        time_since_last_data_packet=TestProcessedDataPacket.time_since_last_data_packet,
    )


class TestProcessedDataPacket:
    """Tests for the ProcessedDataPacket class."""

    current_altitude = 0.0
    vertical_velocity = 0.0
    vertical_acceleration = 0.0
    time_since_last_data_packet = 1

    def test_init(self, processed_data_packet):
        packet = processed_data_packet
        assert packet.current_altitude == self.current_altitude
        assert packet.vertical_velocity == self.vertical_velocity
        assert packet.vertical_acceleration == self.vertical_acceleration
        assert packet.time_since_last_data_packet == self.time_since_last_data_packet

    def test_required_args(self):
        with pytest.raises(TypeError):
            ProcessedDataPacket()
