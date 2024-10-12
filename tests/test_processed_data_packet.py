import pytest

from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket


@pytest.fixture
def processed_data_packet():
    return ProcessedDataPacket(
        avg_acceleration=TestProcessedDataPacket.avg_accel,
        current_altitude=TestProcessedDataPacket.current_altitude,
        speed=TestProcessedDataPacket.speed,
    )


class TestProcessedDataPacket:
    """Tests for the ProcessedDataPacket class."""

    avg_accel = (0.0, 0.0, 0.0)
    current_altitude = 0.0
    speed = 0.0

    def test_init(self, processed_data_packet):
        packet = processed_data_packet
        assert packet.avg_acceleration == self.avg_accel
        assert packet.current_altitude == self.current_altitude
        assert packet.speed_from_acceleration == self.speed

    def test_required_args(self):
        with pytest.raises(TypeError):
            ProcessedDataPacket()
