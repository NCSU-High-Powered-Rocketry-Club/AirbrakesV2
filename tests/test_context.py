"""Tests for IMU packet flow through Context."""

from airbrakes.state import StandbyState
from tests.auxil.utils import make_estimated_data_packet, make_raw_data_packet


class TestContext:
    """Verify context retains raw packets for logging and estimates for processing."""

    def test_init(self, context):
        assert isinstance(context.state, StandbyState)
        assert context.imu_data_packets == []
        assert context.est_data_packets == []

    def test_update_processes_only_estimated_packets(self, context, monkeypatch):
        raw_packet = make_raw_data_packet(timestamp=1)
        estimated_packet = make_estimated_data_packet(timestamp=2, estPressureAlt=100.0)
        context.imu._queue.put(raw_packet)
        context.imu._queue.put(estimated_packet)
        logged_packets = []

        monkeypatch.setattr(
            type(context.logger),
            "log",
            lambda *args: logged_packets.append(args[1:]),
        )
        context.update()

        assert context.imu_data_packets == [raw_packet, estimated_packet]
        assert context.est_data_packets == [estimated_packet]
        assert len(context.processor_data_packets) == 1
        assert logged_packets[0][2] == [raw_packet, estimated_packet]
        assert len(logged_packets[0][3]) == 1

    def test_context_data_packet_records_imu_queue_metrics(self, context):
        context.generate_data_packets()
        assert context.context_data_packet.retrieved_imu_packets == 0
        assert context.context_data_packet.queued_imu_packets == 0
        assert context.context_data_packet.imu_packets_per_cycle == 0
        assert context.context_data_packet.state is StandbyState
