"""Tests for IMU packet handling and Context component lifecycle."""

from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.state import StandbyState
from tests.auxil.utils import make_estimated_data_packet, make_raw_data_packet


class TestContext:
    """Verify Context handles raw and estimated IMU packets independently."""

    def test_init(self, context):
        assert isinstance(context.state, StandbyState)
        assert context.imu_data_packets == []
        assert context.est_data_packets == []
        assert context.processor_data_packets == []
        assert not context.shutdown_requested

    def test_start_stop_starts_all_components_and_is_idempotent(self, context):
        context.start(wait_for_start=True)

        assert context.imu.is_running
        assert context.logger.is_running
        assert context.apogee_predictor.is_running
        assert context.servo.is_powered

        context.stop()
        context.stop()
        assert context.shutdown_requested
        assert not context.imu.is_running
        assert not context.logger.is_running
        assert not context.apogee_predictor.is_running
        assert not context.servo.is_powered

    def test_update_processes_only_estimates_and_logs_original_order(self, context, monkeypatch):
        raw_packet = make_raw_data_packet(timestamp=1)
        estimated_packets = [
            make_estimated_data_packet(timestamp=2, estPressureAlt=100.0),
            make_estimated_data_packet(timestamp=3, estPressureAlt=102.0),
        ]
        for packet in [raw_packet, *estimated_packets]:
            context.imu._queue.put(packet)
        logged_packets = []

        monkeypatch.setattr(
            type(context.logger),
            "log",
            lambda *args: logged_packets.append(args[1:]),
        )
        context.update()

        assert context.imu_data_packets == [raw_packet, *estimated_packets]
        assert context.est_data_packets == estimated_packets
        assert len(context.processor_data_packets) == len(estimated_packets)
        assert logged_packets[0][2] == [raw_packet, *estimated_packets]
        assert len(logged_packets[0][3]) == len(estimated_packets)

    def test_empty_imu_batch_does_not_update_state_or_logger(self, context, monkeypatch):
        calls = []
        monkeypatch.setattr(type(context.state), "update", lambda _: calls.append("state"))
        monkeypatch.setattr(type(context.logger), "log", lambda *_: calls.append("log"))

        context.update()

        assert calls == []

    def test_predictor_path_uses_latest_processed_packet_only(self, context, monkeypatch):
        context.imu._queue.put(make_estimated_data_packet(timestamp=1, estPressureAlt=100.0))
        monkeypatch.setattr(type(context.logger), "log", lambda *_: None)
        context.update()
        sent_packets = []
        monkeypatch.setattr(
            type(context.apogee_predictor),
            "update",
            lambda _, packet: sent_packets.append(packet),
        )

        context.predict_apogee()

        assert sent_packets == [context.processor_data_packets[-1]]

    def test_update_retains_latest_apogee_prediction(self, context, monkeypatch):
        prediction = ApogeePredictorDataPacket(1234.0, 1.0, 2.0, 3.0, 4.0, 5.0)
        context.imu._queue.put(make_raw_data_packet(timestamp=1))
        monkeypatch.setattr(
            type(context.apogee_predictor),
            "get_prediction_data_packet",
            lambda _: prediction,
        )
        monkeypatch.setattr(type(context.logger), "log", lambda *_: None)

        context.update()

        assert context.most_recent_apogee_predictor_data_packet == prediction

    def test_extend_and_retract_notify_processor_and_servo(self, context, monkeypatch):
        calls = []
        monkeypatch.setattr(
            type(context.data_processor),
            "prepare_for_extending_airbrakes",
            lambda _: calls.append("prepare-extend"),
        )
        monkeypatch.setattr(
            type(context.data_processor),
            "prepare_for_retracting_airbrakes",
            lambda _: calls.append("prepare-retract"),
        )
        monkeypatch.setattr(
            type(context.servo),
            "extend_airbrakes",
            lambda _, velocity: calls.append(("extend", velocity)),
        )
        context.servo.set_extension(10)
        monkeypatch.setattr(
            type(context.servo),
            "retract_airbrakes",
            lambda _: calls.append("retract"),
        )

        context.extend_airbrakes(42.0)
        context.retract_airbrakes()

        assert calls == ["prepare-extend", ("extend", 42.0), "prepare-retract", "retract"]

    def test_context_data_packet_records_imu_queue_metrics(self, context):
        context.generate_data_packets()

        assert context.context_data_packet.retrieved_imu_packets == 0
        assert context.context_data_packet.queued_imu_packets == 0
        assert context.context_data_packet.imu_packets_per_cycle == 0
        assert context.context_data_packet.state is StandbyState
