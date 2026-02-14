import contextlib
import queue
import threading
import time
from typing import TYPE_CHECKING

import pytest

from airbrakes.constants import (
    FIRM_SERIAL_TIMEOUT_SECONDS,
    SERVO_DELAY_SECONDS,
    ServoExtension,
)
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.data_handling.packets.context_data_packet import ContextDataPacket
from airbrakes.mock.display import FlightDisplay
from airbrakes.state import CoastState, StandbyState, MotorBurnState
from tests.auxil.utils import (
    make_apogee_predictor_data_packet,
    make_firm_data_packet,
    make_firm_data_packet_zeroed,
)

if TYPE_CHECKING:
    from airbrakes.context import Context


class TestContext:
    """
    Tests the Context class.
    """

    def test_slots(self, context):
        inst = context
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, context):
        assert context.current_extension == ServoExtension.MIN_EXTENSION
        assert isinstance(context.data_processor, DataProcessor)
        assert isinstance(context.state, StandbyState)
        assert isinstance(context.apogee_predictor, ApogeePredictor)
        assert not context.shutdown_requested
        assert not context.firm_data_packets

    def test_set_extension(self, context):
        # Hardcoded calculated values, based on MIN_EXTENSION and MAX_EXTENSION in constants.py
        context.extend_airbrakes()
        assert context.current_extension == ServoExtension.MAX_EXTENSION
        time.sleep(SERVO_DELAY_SECONDS + 0.1)  # wait for servo to extend
        assert context.current_extension == ServoExtension.MAX_EXTENSION
        context.retract_airbrakes()
        assert context.current_extension == ServoExtension.MIN_EXTENSION
        time.sleep(SERVO_DELAY_SECONDS + 0.1)  # wait for servo to extend
        assert context.current_extension == ServoExtension.MIN_EXTENSION

    def test_start(self, context):
        context.start(wait_for_start=True)
        assert context.firm.is_running
        assert context.logger.is_running
        assert context.apogee_predictor.is_running
        context.stop()

    def test_stop_simple(self, context):
        context.start()
        context.stop()
        assert not context.logger.is_running
        assert not context.logger._log_thread.is_alive()
        assert not context.apogee_predictor.is_running
        assert context.current_extension == ServoExtension.MIN_EXTENSION  # set to "0"
        assert context.shutdown_requested
        context.stop()  # Stop again to test idempotency

    def test_airbrakes_ctrl_c_clean_exit_simple(self, context):
        """
        Tests whether the Context handles ctrl+c events correctly.
        """
        context.start()

        try:
            raise KeyboardInterrupt  # send a KeyboardInterrupt to test __exit__
        except KeyboardInterrupt:
            context.stop()

        assert not context.firm.is_running
        assert not context.logger.is_running
        assert not context.apogee_predictor.is_running
        assert context.shutdown_requested

    def test_airbrakes_ctrl_c_exception(self, context):
        """
        Tests whether the AirbrakesContext handles unknown exceptions.
        """
        context.start()
        try:
            raise ValueError("some error in main loop")
        except (KeyboardInterrupt, ValueError):
            pass
        finally:
            context.stop()

        assert not context.firm.is_running
        assert not context.logger.is_running
        assert not context.apogee_predictor.is_running
        assert context.shutdown_requested

    def test_airbrakes_update(
        self,
        monkeypatch,
        random_data_mock_firm,
        context,
    ):
        """
        Tests whether the Airbrakes update method works correctly by calling the relevant methods.

        1. Mock fetching of data packets
        2. Test whether the data processor gets only estimated data packets
        3. Test whether the state machine is updated
        4. Test whether the logger logs the correct data (with correct number and order of packets)
        """
        calls = []
        asserts = []

        def data_processor_update(self, firm_data_packets):
            # monkeypatched method of DataProcessor
            calls.append("update called")
            self._data_packets = firm_data_packets
            # Length of these lists must be equal to the number of estimated data packets for
            # get_processed_data() to work correctly
            self._current_altitudes = [0.0] * len(firm_data_packets)
            self._vertical_velocities = [0.0] * len(firm_data_packets)
            self._vertical_accelerations = [0.0] * len(firm_data_packets)

        def state(self):
            # monkeypatched method of State
            calls.append("state update called")
            if isinstance(self.context.state, CoastState):
                self.context.predict_apogee()
                self.context.current_extension = ServoExtension.MAX_EXTENSION

        def log(self, ctx_dp, servo_dp, firm_data_packets, apg_dps):
            # monkeypatched method of Logger
            calls.append("log called")
            asserts.append(len(firm_data_packets) > 10)
            asserts.append(isinstance(ctx_dp, ContextDataPacket))
            asserts.append(ctx_dp.state == CoastState)
            asserts.append(ctx_dp.retrieved_firm_packets >= 1)
            asserts.append(ctx_dp.apogee_predictor_queue_size >= 0)
            asserts.append(ctx_dp.update_timestamp_ns == pytest.approx(time.time_ns(), rel=1e9))
            asserts.append(servo_dp.set_extension == ServoExtension.MAX_EXTENSION)
            asserts.append(
                firm_data_packets[0].timestamp_seconds == pytest.approx(time.time(), rel=1e9)
            )
            asserts.append(apg_dps is not None)
            asserts.append(apg_dps == make_apogee_predictor_data_packet())
            # More testing of whether we got ApogeePredictorDataPackets is done in
            # `test_airbrakes_receives_apogee_predictor_packets`. The reason why it wasn't tested
            # here is because state.update() is called before apogee_predictor.update(), so the
            # packets aren't sent to the apogee predictor for prediction.

        def apogee_update(self, firm_data_packets):
            calls.append("apogee update called")

        def get_prediction_data_packet(self):
            calls.append("get_prediction_data_packet called")
            return make_apogee_predictor_data_packet()

        mocked_airbrakes = context
        mocked_airbrakes.firm = random_data_mock_firm
        mocked_airbrakes.state = CoastState(
            mocked_airbrakes
        )  # Set to coast state to test apogee update
        mocked_airbrakes.start(wait_for_start=True)

        time.sleep(0.7)  # Sleep a bit so that the FIRM queue is being filled

        assert (
            mocked_airbrakes.firm._queue.qsize() > 0
        )  # just testing that our mocked firm is working
        assert mocked_airbrakes.state.name == "CoastState"
        assert mocked_airbrakes.data_processor._last_data_packet is None

        monkeypatch.setattr(context.data_processor.__class__, "update", data_processor_update)
        monkeypatch.setattr(context.apogee_predictor.__class__, "update", apogee_update)
        monkeypatch.setattr(mocked_airbrakes.state.__class__, "update", state)
        monkeypatch.setattr(context.logger.__class__, "log", log)
        monkeypatch.setattr(
            context.apogee_predictor.__class__,
            "get_prediction_data_packet",
            get_prediction_data_packet,
        )

        # Let's call .update() and check if stuff was called and/or changed:
        mocked_airbrakes.update()

        assert len(calls) == 5
        assert calls == [
            "update called",
            "get_prediction_data_packet called",
            "state update called",
            "apogee update called",
            "log called",
        ]
        assert all(asserts)
        assert (
            mocked_airbrakes.most_recent_apogee_predictor_data_packet
            == make_apogee_predictor_data_packet()
        )

        mocked_airbrakes.stop()

    def test_stop_with_random_data_firm_and_update(self, context: Context, random_data_mock_firm):
        """
        Tests stopping of the airbrakes system while we are using the FIRM and calling
        airbrakes.update().
        """
        context.firm = random_data_mock_firm
        has_airbrakes_stopped = threading.Event()
        started_thread = False

        def stop_airbrakes():
            context.stop()  # Happens when LandedState requests shutdown in the real flight
            has_airbrakes_stopped.set()

        context.start(wait_for_start=True)

        while not context.shutdown_requested:
            with contextlib.suppress(queue.Empty):
                context.update()

            if not started_thread:
                started_thread = True
                stop_airbrakes_thread = threading.Timer(0.1, stop_airbrakes)
                stop_airbrakes_thread.start()

        # Wait for the airbrakes to stop. If the stopping took too long, that means something is
        # wrong with the stopping thread. We don't want to hit the "just in case" timeout
        # in `get_data_packets`.
        has_airbrakes_stopped.wait(FIRM_SERIAL_TIMEOUT_SECONDS - 0.4)
        assert not context.firm.is_running
        assert not context.logger.is_running
        assert not context.apogee_predictor.is_running
        assert not context.logger._log_thread.is_alive()
        assert not context.apogee_predictor._prediction_thread.is_alive()
        assert context.current_extension in ServoExtension.MIN_EXTENSION

        # Open the file and check if we have a large number of lines:
        with context.logger.log_path.open() as file:
            lines = file.readlines()
            assert len(lines) > 20

    def test_stop_with_display_and_update_loop(
        self, context: Context, random_data_mock_firm, mocked_args_parser, capsys
    ):
        """
        Tests stopping of the airbrakes system while we are using the FIRM, the flight display, and
        calling airbrakes.update().
        """
        context.firm = random_data_mock_firm
        fd = FlightDisplay(context=context, args=mocked_args_parser)
        has_airbrakes_stopped = threading.Event()
        started_thread = False

        def stop_airbrakes():
            fd.end_mock_interrupted.set()
            fd.stop()
            context.stop()  # Happens when LandedState requests shutdown in the real flight
            has_airbrakes_stopped.set()

        context.start()
        fd.start()

        while not context.shutdown_requested:
            context.update()

            if not started_thread:
                started_thread = True
                stop_airbrakes_thread = threading.Timer(0.75, stop_airbrakes)
                stop_airbrakes_thread.start()

        # Wait for the airbrakes to stop. If the stopping took too long, that means something is
        # wrong with the stopping thread. We don't want to hit the "just in case" timeout
        # in `get_data_packets`.
        has_airbrakes_stopped.wait(FIRM_SERIAL_TIMEOUT_SECONDS - 0.4)
        assert not context.firm.is_running
        assert not context.logger.is_running
        assert not context.apogee_predictor.is_running
        assert not context.logger._log_thread.is_alive()
        assert not context.apogee_predictor._prediction_thread.is_alive()
        assert context.current_extension in ServoExtension.MIN_EXTENSION

        assert not fd._running

        # Open the file and check if we have a large number of lines:
        with context.logger.log_path.open() as file:
            lines = file.readlines()
            assert len(lines) > 20

        # Check display output:
        captured = capsys.readouterr()
        assert "REPLAY INFO" in captured.out

    def test_airbrakes_sends_packets_to_apogee_predictor(
        self,
        monkeypatch,
        idle_mock_firm,
        logger,
        context,
    ):
        """
        Tests whether the airbrakes predict_apogee method works correctly by calling the relevant
        methods.

        1. Mock fetching of data packets
        2. Test whether the apogee predictor gets only estimated data packets and not duplicated
            data.
        """
        calls = []
        packets = []

        def fake_log(self, *args, **kwargs):
            pass

        def apogee_update(self, firm_data_packets):
            packets.append(firm_data_packets)
            calls.append("apogee update called")

        context.firm = idle_mock_firm
        context.start()

        time.sleep(0.01)

        assert not context.firm._queue.qsize()
        assert context.state.name == "StandbyState"
        assert not context.most_recent_apogee_predictor_data_packet

        monkeypatch.setattr(context.apogee_predictor.__class__, "update", apogee_update)
        monkeypatch.setattr(logger.__class__, "log", fake_log)

        # Insert 1 firm data packet
        firm_data_packet_1 = make_firm_data_packet(timestamp_seconds=time.time())
        context.firm._queue.put(firm_data_packet_1)
        time.sleep(0.001)  # Wait for queue to be filled, and airbrakes.update to process it
        context.update()
        # Check if we processed the firm data packet:
        assert list(context.firm_data_packets) == [firm_data_packet_1]
        assert not context.most_recent_apogee_predictor_data_packet
        # There should be no calls or packets, because we are in StandbyState
        assert context.state.name == "StandbyState"
        assert not calls
        assert not packets

        # Now go to motor burn, still no apogee prediction should happen
        context.state = MotorBurnState(context=context)
        # Insert 1 firm data packet
        firm_data_packet_2 = make_firm_data_packet(timestamp_seconds=time.time())
        context.firm._queue.put(firm_data_packet_2)
        time.sleep(0.001)  # Wait for queue to be filled, and airbrakes.update to process it
        context.update()
        # There should be no calls or packets, because we are in MotorBurnState
        assert not calls
        assert not packets

        # Now go to coast burn we should see apogee prediction happening
        context.state = CoastState(context=context)
        assert context.state.name == "CoastState"

        # Insert 2 more firm data packets
        firm_data_packet_2 = make_firm_data_packet_zeroed(
            timestamp_seconds=1.00001,
            est_position_z_meters=20.0,
            est_velocity_z_meters_per_s=0.0,
        )

        firm_data_packet_3 = make_firm_data_packet_zeroed(
            timestamp_seconds=1.00004,
            est_position_z_meters=24.0,
            est_velocity_z_meters_per_s=0.0,
        )

        context.firm._queue.put(firm_data_packet_2)
        context.firm._queue.put(firm_data_packet_3)
        time.sleep(0.001)
        context.update()
        time.sleep(0.01)
        # Now we should have calls and packets, because we are in CoastState
        assert list(context.firm_data_packets) == [firm_data_packet_2, firm_data_packet_3]

        # Let's call .predict_apogee() and check if stuff was called and/or changed:
        context.predict_apogee()
        # It's 2, one from when it was called in update(), and once from here:
        assert len(calls) == 2
        assert calls == ["apogee update called"] * 2

        context.stop()

    def test_airbrakes_receives_apogee_predictor_packet(
        self, context: Context, monkeypatch, random_data_mock_firm
    ):
        """
        Tests whether the airbrakes receives packets from the apogee predictor and that the
        attribute `predicted_apogee` is updated correctly.
        """
        monkeypatch.setattr(context, "firm", random_data_mock_firm)

        context.start(wait_for_start=True)
        time.sleep(0.1)

        context.firm_data_packets = [make_firm_data_packet()]

        # Now we will have enough packets to run the apogee predictor:
        context.predict_apogee()

        # Nothing should be fetched yet:
        assert not context.most_recent_apogee_predictor_data_packet

        time.sleep(0.1)  # sleep so apogee prediction runs
        apg_packet = context.apogee_predictor.get_prediction_data_packet()
        context.most_recent_apogee_predictor_data_packet = apg_packet

        context.stop()

        assert isinstance(
            context.most_recent_apogee_predictor_data_packet, ApogeePredictorDataPacket
        )

        assert context.most_recent_apogee_predictor_data_packet.predicted_apogee is not None
        assert (
            context.most_recent_apogee_predictor_data_packet.height_used_for_prediction is not None
        )
        assert (
            context.most_recent_apogee_predictor_data_packet.velocity_used_for_prediction
            is not None
        )

    def test_generate_data_packets(self, context):
        """
        Tests whether the airbrakes generates the correct data packets for logging.
        """
        context.generate_data_packets()
        assert context.context_data_packet.state == StandbyState
        assert context.context_data_packet.retrieved_firm_packets == 0
        assert context.context_data_packet.apogee_predictor_queue_size >= 0
        assert context.context_data_packet.update_timestamp_ns == pytest.approx(
            time.time_ns(), rel=1e9
        )
        assert context.servo_data_packet.set_extension == ServoExtension.MIN_EXTENSION

    def test_benchmark_airbrakes_update(self, context, benchmark, random_data_mock_firm):
        """
        Benchmark the update method of the airbrakes system.
        """
        # uv managed arm64 python is still not built with JIT, thus this is commented out.
        # if _testinternalcapi.get_optimizer() is None:
        #     pytest.fail("Please run benchmarks with PYTHON_JIT=1!")
        ab = context
        ab.firm = random_data_mock_firm
        ab.start()
        time.sleep(0.05)  # Sleep a bit so that the FIRM queue is being filled
        benchmark(context.update)
        ab.stop()
