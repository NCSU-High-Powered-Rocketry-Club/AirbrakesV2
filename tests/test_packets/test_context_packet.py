import pytest

from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket


@pytest.fixture
def context_packet():
    return ContextDataPacket(
        batch_number=0,
        state_letter="S",
        imu_queue_size=1,
        apogee_predictor_queue_size=1,
    )


class TestContextDataPacket:
    """Tests for the ContextDataPacket class."""

    batch_number = 0
    state_letter = "S"
    imu_queue_size = 1
    apogee_predictor_queue_size = 1

    def test_init(self, context_packet):
        packet = context_packet
        assert packet.batch_number == self.batch_number
        assert packet.state_letter == self.state_letter
        assert packet.imu_queue_size == self.imu_queue_size
        assert packet.apogee_predictor_queue_size == self.apogee_predictor_queue_size

    def test_required_args(self):
        with pytest.raises(TypeError):
            ContextDataPacket()
