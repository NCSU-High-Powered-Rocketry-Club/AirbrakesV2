import pytest

from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket


@pytest.fixture
def context_packet():
    return ContextDataPacket(
        state_letter="S",
        fetched_packets_in_main=0,
        imu_queue_size=1,
        apogee_predictor_queue_size=1,
        fetched_imu_packets=2,
        update_timestamp_ns=4782379489276,
    )


class TestContextDataPacket:
    """Tests for the ContextDataPacket class."""

    fetched_packets_in_main = 0
    state_letter = "S"
    imu_queue_size = 1
    apogee_predictor_queue_size = 1
    fetched_imu_packets = 2
    update_timestamp = 4782379489276

    def test_init(self, context_packet):
        packet = context_packet
        assert packet.state_letter == self.state_letter
        assert packet.fetched_packets_in_main == self.fetched_packets_in_main
        assert packet.imu_queue_size == self.imu_queue_size
        assert packet.apogee_predictor_queue_size == self.apogee_predictor_queue_size
        assert packet.fetched_imu_packets == self.fetched_imu_packets
        assert packet.update_timestamp_ns == self.update_timestamp

    def test_required_args(self):
        with pytest.raises(TypeError):
            ContextDataPacket()
