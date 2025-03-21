# import _testinternalcapi
import threading
import time

import pytest

from airbrakes.constants import (
    APOGEE_PREDICTION_MIN_PACKETS,
    IMU_TIMEOUT_SECONDS,
    SERVO_DELAY_SECONDS,
    ServoExtension,
)
from airbrakes.context import AirbrakesContext
from airbrakes.hardware.camera import Camera
from airbrakes.mock.display import FlightDisplay
from airbrakes.state import CoastState, StandbyState
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.telemetry.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket
from airbrakes.telemetry.packets.context_data_packet import ContextDataPacket
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket
from tests.auxil.utils import (
    make_apogee_predictor_data_packet,
    make_est_data_packet,
    make_processor_data_packet,
    make_raw_data_packet,
)


class TestAirbrakesContext:
    """Tests the AirbrakesContext class"""

    def test_slots(self, airbrakes):
        inst = airbrakes
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(
        self, airbrakes, logger, imu, servo, data_processor, apogee_predictor, mock_camera
    ):
        assert airbrakes.logger == logger
        assert airbrakes.servo == servo
        assert airbrakes.imu == imu
        assert airbrakes.apogee_predictor == apogee_predictor
        assert airbrakes.camera == mock_camera
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        assert airbrakes.data_processor == data_processor
        assert isinstance(airbrakes.data_processor, DataProcessor)
        assert isinstance(airbrakes.state, StandbyState)
        assert isinstance(airbrakes.apogee_predictor, ApogeePredictor)
        assert isinstance(airbrakes.camera, Camera)
        assert not airbrakes.shutdown_requested
        assert not airbrakes.est_data_packets

    def test_set_extension(self, airbrakes):
        # Hardcoded calculated values, based on MIN_EXTENSION and MAX_EXTENSION in constants.py
        airbrakes.extend_airbrakes()
        assert airbrakes.servo.current_extension == ServoExtension.MAX_EXTENSION
        time.sleep(SERVO_DELAY_SECONDS + 0.1)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MAX_NO_BUZZ
        airbrakes.retract_airbrakes()
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        time.sleep(SERVO_DELAY_SECONDS + 0.1)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ

    def test_start(self, airbrakes):
        airbrakes.start()
        assert airbrakes.imu.is_running
        assert airbrakes.logger.is_running
        assert airbrakes.apogee_predictor.is_running
        # assert airbrakes.camera.is_running
        airbrakes.stop()

    def test_stop_simple(self, airbrakes):
        airbrakes.start()
        airbrakes.stop()
        assert not airbrakes.imu.is_running
        assert not airbrakes.logger.is_running
        assert not airbrakes.imu._running.value
        assert not airbrakes.imu._data_fetch_process.is_alive()
        assert not airbrakes.logger._log_process.is_alive()
        assert not airbrakes.apogee_predictor.is_running
        assert not airbrakes.camera.is_running
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION  # set to "0"
        assert airbrakes.shutdown_requested
        airbrakes.stop()  # Stop again to test idempotency

    def test_airbrakes_ctrl_c_clean_exit_simple(self, airbrakes):
        """Tests whether the AirbrakesContext handles ctrl+c events correctly."""
        airbrakes.start()

        try:
            raise KeyboardInterrupt  # send a KeyboardInterrupt to test __exit__
        except KeyboardInterrupt:
            airbrakes.stop()

        assert not airbrakes.imu.is_running
        assert not airbrakes.logger.is_running
        assert not airbrakes.apogee_predictor.is_running
        assert not airbrakes.camera.is_running
        assert airbrakes.shutdown_requested

    def test_airbrakes_ctrl_c_exception(self, airbrakes):
        """Tests whether the AirbrakesContext handles unknown exceptions."""

        airbrakes.start()
        try:
            raise ValueError("some error in main loop")
        except (KeyboardInterrupt, ValueError):
            pass
        finally:
            airbrakes.stop()

        assert not airbrakes.imu.is_running
        assert not airbrakes.logger.is_running
        assert not airbrakes.apogee_predictor.is_running
        assert not airbrakes.camera.is_running
        assert airbrakes.shutdown_requested

    def test_airbrakes_update(
        self,
        monkeypatch,
        random_data_mock_imu,
        airbrakes,
    ):
        """Tests whether the Airbrakes update method works correctly by calling the relevant methods

        1. Mock fetching of data packets
        2. Test whether the data processor gets only estimated data packets
        3. Test whether the state machine is updated
        4. Test whether the logger logs the correct data (with correct number and order of packets)
        """
        calls = []
        asserts = []

        def data_processor_update(self, est_data_packets):
            # monkeypatched method of IMUDataProcessor
            calls.append("update called")
            self._data_packets = est_data_packets
            # Length of these lists must be equal to the number of estimated data packets for
            # get_processed_data() to work correctly
            self._current_altitudes = [0.0] * len(est_data_packets)
            self._vertical_velocities = [0.0] * len(est_data_packets)
            self._rotated_accelerations = [0.0] * len(est_data_packets)
            self._time_differences = [0.0] * len(est_data_packets)

        def state(self):
            # monkeypatched method of State
            calls.append("state update called")
            if isinstance(self.context.state, CoastState):
                self.context.predict_apogee()
                self.context.servo.current_extension = ServoExtension.MAX_EXTENSION

        def log(self, ctx_dp, servo_dp, imu_data_packets, processor_data_packets, apg_dps):
            # monkeypatched method of Logger
            calls.append("log called")
            asserts.append(len(imu_data_packets) > 10)
            asserts.append(isinstance(ctx_dp, ContextDataPacket))
            asserts.append(
                ctx_dp.state_letter == "C"
                and ctx_dp.retrieved_imu_packets >= 1
                and ctx_dp.queued_imu_packets > 0
                and ctx_dp.apogee_predictor_queue_size >= 0
                and ctx_dp.imu_packets_per_cycle >= 0  # mock imus will be 0
                and ctx_dp.update_timestamp_ns == pytest.approx(time.time_ns(), rel=1e9)
            )
            asserts.append(servo_dp.set_extension == str(ServoExtension.MAX_EXTENSION.value))
            asserts.append(imu_data_packets[0].timestamp == pytest.approx(time.time_ns(), rel=1e9))
            asserts.append(processor_data_packets[0].current_altitude == 0.0)
            asserts.append(isinstance(apg_dps, list))
            asserts.append(len(apg_dps) >= 0)
            asserts.append(apg_dps[-1] == make_apogee_predictor_data_packet())
            # More testing of whether we got ApogeePredictorDataPackets is done in
            # `test_airbrakes_receives_apogee_predictor_packets`. The reason why it wasn't tested
            # here is because state.update() is called before apogee_predictor.update(), so the
            # packets aren't sent to the apogee predictor for prediction.

        def apogee_update(self, processor_data_packets):
            calls.append("apogee update called")

        def get_prediction_data_packets(self):
            calls.append("get_prediction_data_packets called")
            return [make_apogee_predictor_data_packet()]

        mocked_airbrakes = airbrakes
        mocked_airbrakes.imu = random_data_mock_imu
        mocked_airbrakes.state = CoastState(
            mocked_airbrakes
        )  # Set to coast state to test apogee update
        mocked_airbrakes.start()

        time.sleep(0.05)  # Sleep a bit so that the IMU queue is being filled

        assert mocked_airbrakes.imu._queued_imu_packets.qsize() > 0
        assert mocked_airbrakes.state.name == "CoastState"
        assert mocked_airbrakes.data_processor._last_data_packet is None

        monkeypatch.setattr(airbrakes.data_processor.__class__, "update", data_processor_update)
        monkeypatch.setattr(airbrakes.apogee_predictor.__class__, "update", apogee_update)
        monkeypatch.setattr(mocked_airbrakes.state.__class__, "update", state)
        monkeypatch.setattr(airbrakes.logger.__class__, "log", log)
        monkeypatch.setattr(
            airbrakes.apogee_predictor.__class__,
            "get_prediction_data_packets",
            get_prediction_data_packets,
        )

        # Let's call .update() and check if stuff was called and/or changed:
        mocked_airbrakes.update()

        assert len(calls) == 5
        assert calls == [
            "update called",
            "get_prediction_data_packets called",
            "state update called",
            "apogee update called",
            "log called",
        ]
        assert all(asserts)
        assert mocked_airbrakes.last_apogee_predictor_packet == make_apogee_predictor_data_packet()

        mocked_airbrakes.stop()

    def test_stop_with_random_data_imu_and_update(
        self, airbrakes: AirbrakesContext, random_data_mock_imu
    ):
        """Tests stopping of the airbrakes system while we are using the IMU and
        calling airbrakes.update().
        """
        airbrakes.imu = random_data_mock_imu
        has_airbrakes_stopped = threading.Event()
        started_thread = False

        def stop_airbrakes():
            airbrakes.stop()  # Happens when LandedState requests shutdown in the real flight
            has_airbrakes_stopped.set()

        airbrakes.start()

        while not airbrakes.shutdown_requested:
            airbrakes.update()

            if not started_thread:
                started_thread = True
                stop_airbrakes_thread = threading.Timer(0.1, stop_airbrakes)
                stop_airbrakes_thread.start()

        # Wait for the airbrakes to stop. If the stopping took too long, that means something is
        # wrong with the stopping process. We don't want to hit the "just in case" timeout
        # in `get_imu_data_packets`.
        has_airbrakes_stopped.wait(IMU_TIMEOUT_SECONDS - 0.4)
        assert not airbrakes.imu.is_running
        assert not airbrakes.logger.is_running
        assert not airbrakes.apogee_predictor.is_running
        assert not airbrakes.imu._running.value
        assert not airbrakes.imu._data_fetch_process.is_alive()
        assert not airbrakes.logger._log_process.is_alive()
        assert not airbrakes.apogee_predictor._prediction_process.is_alive()
        assert airbrakes.servo.current_extension in (
            ServoExtension.MIN_EXTENSION,
            ServoExtension.MIN_NO_BUZZ,
        )

        # Open the file and check if we have a large number of lines:
        with airbrakes.logger.log_path.open() as file:
            lines = file.readlines()
            assert len(lines) > 100

    def test_stop_with_display_and_update_loop(
        self, airbrakes: AirbrakesContext, random_data_mock_imu, mocked_args_parser, capsys
    ):
        """Tests stopping of the airbrakes system while we are using the IMU, the flight display,
        and calling airbrakes.update().
        """
        airbrakes.imu = random_data_mock_imu
        fd = FlightDisplay(context=airbrakes, start_time=time.time(), args=mocked_args_parser)
        has_airbrakes_stopped = threading.Event()
        started_thread = False

        def stop_airbrakes():
            fd.end_mock_interrupted.set()
            fd.stop()
            airbrakes.stop()  # Happens when LandedState requests shutdown in the real flight
            has_airbrakes_stopped.set()

        airbrakes.start()
        fd.start()

        while not airbrakes.shutdown_requested:
            airbrakes.update()

            if not started_thread:
                started_thread = True
                stop_airbrakes_thread = threading.Timer(0.1, stop_airbrakes)
                stop_airbrakes_thread.start()

        # Wait for the airbrakes to stop. If the stopping took too long, that means something is
        # wrong with the stopping process. We don't want to hit the "just in case" timeout
        # in `get_imu_data_packets`.
        has_airbrakes_stopped.wait(IMU_TIMEOUT_SECONDS - 0.4)
        assert not airbrakes.imu.is_running
        assert not airbrakes.logger.is_running
        assert not airbrakes.apogee_predictor.is_running
        assert not airbrakes.imu._running.value
        assert not airbrakes.camera.is_running
        assert not airbrakes.imu._data_fetch_process.is_alive()
        assert not airbrakes.logger._log_process.is_alive()
        assert not airbrakes.apogee_predictor._prediction_process.is_alive()
        assert not airbrakes.camera.camera_control_process.is_alive()
        assert airbrakes.servo.current_extension in (
            ServoExtension.MIN_EXTENSION,
            ServoExtension.MIN_NO_BUZZ,
        )

        assert not fd._running

        # Open the file and check if we have a large number of lines:
        with airbrakes.logger.log_path.open() as file:
            lines = file.readlines()
            assert len(lines) > 100

        # Check display output:
        captured = capsys.readouterr()
        assert "REPLAY INFO" in captured.out

    def test_airbrakes_sends_packets_to_apogee_predictor(
        self,
        monkeypatch,
        idle_mock_imu,
        logger,
        airbrakes,
    ):
        """Tests whether the airbrakes predict_apogee method works correctly by calling the
        relevant methods.

        1. Mock fetching of data packets
        2. Test whether the apogee predictor gets only estimated data packets and not duplicated
            data.
        """
        calls = []
        packets = []

        def fake_log(self, *args, **kwargs):
            pass

        def apogee_update(self, processor_data_packets):
            packets.extend(processor_data_packets)
            calls.append("apogee update called")

        airbrakes.imu = idle_mock_imu
        airbrakes.start()

        time.sleep(0.01)

        assert not airbrakes.imu._queued_imu_packets.qsize()
        assert airbrakes.state.name == "StandbyState"
        assert airbrakes.data_processor._last_data_packet is None
        assert not airbrakes.apogee_predictor_data_packets

        monkeypatch.setattr(airbrakes.apogee_predictor.__class__, "update", apogee_update)
        monkeypatch.setattr(logger.__class__, "log", fake_log)

        # Insert 1 raw, then 2 estimated, then 1 raw data packet:
        raw_1 = make_raw_data_packet(timestamp=time.time_ns())
        airbrakes.imu._queued_imu_packets.put(raw_1)
        time.sleep(0.001)  # Wait for queue to be filled, and airbrakes.update to process it
        airbrakes.update()
        # Check if we processed the raw data packet:
        assert list(airbrakes.imu_data_packets) == [raw_1]
        assert not airbrakes.est_data_packets
        assert len(airbrakes.processor_data_packets) == 0
        assert not airbrakes.apogee_predictor_data_packets
        # Let's call .predict_apogee() and check if stuff was called and/or changed:
        airbrakes.predict_apogee()
        assert not calls
        assert not packets

        # Insert 2 estimated data packet:
        # first_update():
        est_1 = make_est_data_packet(
            timestamp=int(1 + 1e9),
            estPressureAlt=20.0,
            estOrientQuaternionW=0.99,
            estOrientQuaternionX=0.1,
            estOrientQuaternionY=0.2,
            estOrientQuaternionZ=0.3,
        )
        est_2 = make_est_data_packet(timestamp=int(3 + 1e9), estPressureAlt=24.0)
        airbrakes.imu._queued_imu_packets.put(est_1)
        airbrakes.imu._queued_imu_packets.put(est_2)
        time.sleep(0.001)
        airbrakes.update()
        time.sleep(0.01)
        # Check if we processed the estimated data packet:
        assert list(airbrakes.imu_data_packets) == [est_1, est_2]
        assert airbrakes.est_data_packets == [est_1, est_2]
        assert len(airbrakes.processor_data_packets) == 2
        assert airbrakes.processor_data_packets[-1].current_altitude == 2.0
        assert float(
            airbrakes.processor_data_packets[-1].time_since_last_data_packet
        ) == pytest.approx(2.0 + 1e-9, rel=1e1)
        # Let's call .predict_apogee() and check if stuff was called and/or changed:
        airbrakes.predict_apogee()
        assert len(calls) == 1
        assert calls == ["apogee update called"]
        assert len(packets) == 2
        assert packets[-1].current_altitude == 2.0

        # Insert 1 raw data packet:
        raw_2 = make_raw_data_packet(timestamp=time.time_ns())
        airbrakes.imu._queued_imu_packets.put(raw_2)
        time.sleep(0.001)
        airbrakes.update()
        # Check if we processed the raw data packet:
        assert list(airbrakes.imu_data_packets) == [raw_2]
        assert not airbrakes.est_data_packets
        assert airbrakes.processor_data_packets[-1].current_altitude == 2.0
        assert float(
            airbrakes.processor_data_packets[-1].time_since_last_data_packet
        ) == pytest.approx(2.0 + 1e-9, rel=1e1)
        # Let's call .predict_apogee() and check if stuff was called and/or changed:
        airbrakes.predict_apogee()
        assert len(calls) == 1
        assert calls == ["apogee update called"]
        assert len(packets) == 2
        assert packets[-1].current_altitude == 2.0
        # That ensures that we don't send duplicate data to the predictor.

        airbrakes.stop()

    def test_airbrakes_receives_apogee_predictor_packets(
        self, airbrakes: AirbrakesContext, monkeypatch, random_data_mock_imu
    ):
        """Tests whether the airbrakes receives packets from the apogee predictor and that the
        attribute `predicted_apogee` is updated correctly."""

        monkeypatch.setattr("airbrakes.interfaces.base_imu.MAX_FETCHED_PACKETS", 100)
        monkeypatch.setattr(airbrakes, "imu", random_data_mock_imu)

        airbrakes.start()
        time.sleep(0.01)
        # Need to assert that we have these many packets otherwise apogee prediction won't run:
        assert airbrakes.imu.queued_imu_packets > APOGEE_PREDICTION_MIN_PACKETS

        # We have to do this convoluted manual way of updating instead of airbrakes.update() because
        # 1) faster-fifo does not guarantee that all packets will be fetched in a single get_many()
        # call.
        # 2) We don't want other things in airbrakes.update() to execute, like the state machine.
        est_packets = 0
        while est_packets < APOGEE_PREDICTION_MIN_PACKETS:
            fetched = airbrakes.imu.get_imu_data_packets()
            est_data_packets = [x for x in fetched if isinstance(x, EstimatedDataPacket)]
            airbrakes.est_data_packets.extend(est_data_packets)
            airbrakes.data_processor.update(est_data_packets)
            if est_data_packets:
                # Generate dummy pdps:
                pdps = [make_processor_data_packet() for _ in range(len(est_data_packets))]
                airbrakes.processor_data_packets.extend(pdps)
            est_packets += len(est_data_packets)

        # Now we will have enough packets to run the apogee predictor:
        airbrakes.predict_apogee()
        # Nothing should be fetched yet:
        assert not airbrakes.apogee_predictor_data_packets

        time.sleep(0.01)  # sleep so apogee prediction runs
        apg_packets = airbrakes.apogee_predictor.get_prediction_data_packets()
        airbrakes.apogee_predictor_data_packets.extend(apg_packets)
        airbrakes.last_apogee_predictor_packet = apg_packets[-1]

        airbrakes.stop()

        assert len(apg_packets) > 0
        ap_dp: ApogeePredictorDataPacket = apg_packets[0]
        assert isinstance(ap_dp, ApogeePredictorDataPacket)
        # Our apogee may or may not converge, depending on the number of packets/data in them,
        # so just check if we have some values:
        assert ap_dp.uncertainty_threshold_1
        assert ap_dp.uncertainty_threshold_2
        assert ap_dp.predicted_apogee is not None
        assert airbrakes.last_apogee_predictor_packet.predicted_apogee is not None

        # Test that a reset of the list of apogee_predictor_data_packets doesn't reset the
        # predicted_apogee attribute:
        airbrakes.apogee_predictor_data_packets = []
        assert airbrakes.last_apogee_predictor_packet.predicted_apogee is not None

    def test_generate_data_packets(self, airbrakes):
        """Tests whether the airbrakes generates the correct data packets for logging."""
        airbrakes.generate_data_packets()
        assert airbrakes.context_data_packet.state_letter == "S"
        assert airbrakes.context_data_packet.retrieved_imu_packets == 0
        assert airbrakes.context_data_packet.queued_imu_packets >= 0
        assert airbrakes.context_data_packet.apogee_predictor_queue_size >= 0
        assert airbrakes.context_data_packet.imu_packets_per_cycle >= 0
        assert airbrakes.context_data_packet.update_timestamp_ns == pytest.approx(
            time.time_ns(), rel=1e9
        )
        assert airbrakes.servo_data_packet.set_extension == str(ServoExtension.MIN_EXTENSION.value)

    def test_benchmark_airbrakes_update(self, airbrakes, benchmark, random_data_mock_imu):
        """Benchmark the update method of the airbrakes system."""
        # uv managed arm64 python is still not built with JIT, thus this is commented out.
        # if _testinternalcapi.get_optimizer() is None:
        #     pytest.fail("Please run benchmarks with PYTHON_JIT=1!")
        ab = airbrakes
        ab.imu = random_data_mock_imu
        ab.start()
        time.sleep(0.05)  # Sleep a bit so that the IMU queue is being filled
        benchmark(airbrakes.update)
        ab.stop()
