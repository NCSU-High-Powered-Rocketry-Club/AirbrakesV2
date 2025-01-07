import pytest

from airbrakes.data_handling.packets.context_data_packet import ContextPacket


@pytest.fixture
def debug_packet():
    return ContextPacket(
        predicted_apogee=TestDebugPacket.predicted_apogee,
        uncertainity_threshold_1=TestDebugPacket.uncertainity_threshold_1,
        uncertainity_threshold_2=TestDebugPacket.uncertainity_threshold_2,
        fetched_imu_packets=TestDebugPacket.fetched_imu_packets,
        packets_in_imu_queue=TestDebugPacket.packets_in_imu_queue,
    )


class TestDebugPacket:
    """Tests for the ProcessedDataPacket class."""

    predicted_apogee = 0.0
    uncertainity_threshold_1 = 1.0
    uncertainity_threshold_2 = 2.0
    fetched_imu_packets = 1
    packets_in_imu_queue = 1

    def test_init(self, debug_packet):
        packet = debug_packet
        assert packet.predicted_apogee == self.predicted_apogee
        assert packet.uncertainity_threshold_1 == self.uncertainity_threshold_1
        assert packet.uncertainity_threshold_2 == self.uncertainity_threshold_2
        assert packet.fetched_imu_packets == self.fetched_imu_packets
        assert packet.packets_in_imu_queue == self.packets_in_imu_queue

    def test_required_args(self):
        with pytest.raises(TypeError):
            ContextPacket()
