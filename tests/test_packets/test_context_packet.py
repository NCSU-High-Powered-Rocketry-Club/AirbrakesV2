import pytest

from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket


@pytest.fixture
def context_packet():
    return ContextDataPacket(
        state_letter="S",
        retrieved_imu_packets=0,
        queued_imu_packets=1,
        apogee_predictor_queue_size=1,
        imu_packets_per_cycle=2,
        update_timestamp_ns=4782379489276,
    )


class TestContextDataPacket:
    """Tests for the ContextDataPacket class."""

    retrieved_imu_packets = 0
    state_letter = "S"
    queued_imu_packets = 1
    apogee_predictor_queue_size = 1
    imu_packets_per_cycle = 2
    update_timestamp = 4782379489276

    def test_init(self, context_packet):
        packet = context_packet
        assert packet.state_letter == self.state_letter
        assert packet.retrieved_imu_packets == self.retrieved_imu_packets
        assert packet.queued_imu_packets == self.queued_imu_packets
        assert packet.apogee_predictor_queue_size == self.apogee_predictor_queue_size
        assert packet.imu_packets_per_cycle == self.imu_packets_per_cycle
        assert packet.update_timestamp_ns == self.update_timestamp

    def test_required_args(self):
        with pytest.raises(TypeError):
            ContextDataPacket()
