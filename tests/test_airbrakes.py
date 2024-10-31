import time

import pytest

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.state import CoastState, StandbyState
from constants import SERVO_DELAY, ServoExtension


class TestAirbrakesContext:
    """Tests the AirbrakesContext class"""

    def test_slots(self, airbrakes):
        inst = airbrakes
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, airbrakes, logger, imu, servo, data_processor):
        assert airbrakes.logger == logger
        assert airbrakes.servo == servo
        assert airbrakes.imu == imu
        assert airbrakes.current_extension == ServoExtension.MIN_EXTENSION
        assert airbrakes.data_processor == data_processor
        assert isinstance(airbrakes.data_processor, IMUDataProcessor)
        assert isinstance(airbrakes.state, StandbyState)
        assert not airbrakes.shutdown_requested

    def test_set_extension(self, airbrakes):
        # Hardcoded calculated values, based on MIN_EXTENSION and MAX_EXTENSION in constants.py
        airbrakes.extend_airbrakes()
        assert airbrakes.servo.current_extension == ServoExtension.MAX_EXTENSION
        time.sleep(SERVO_DELAY + 0.1)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MAX_NO_BUZZ
        airbrakes.retract_airbrakes()
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        time.sleep(SERVO_DELAY + 0.1)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ

    def test_start(self, airbrakes):
        airbrakes.start()
        assert airbrakes.imu.is_running
        assert airbrakes.logger.is_running
        airbrakes.stop()

    def test_stop(self, airbrakes):
        airbrakes.start()
        airbrakes.stop()
        assert not airbrakes.imu.is_running
        assert not airbrakes.logger.is_running
        assert not airbrakes.imu._running.value
        assert not airbrakes.imu._data_fetch_process.is_alive()
        assert not airbrakes.logger._log_process.is_alive()
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION  # set to "0"
        assert airbrakes.shutdown_requested

    def test_airbrakes_ctrl_c_clean_exit(self, airbrakes):
        """Tests whether the AirbrakesContext handles ctrl+c events correctly."""
        airbrakes.start()

        try:
            raise KeyboardInterrupt  # send a KeyboardInterrupt to test __exit__
        except KeyboardInterrupt:
            airbrakes.stop()

        assert not airbrakes.imu.is_running
        assert not airbrakes.logger.is_running
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
        assert airbrakes.shutdown_requested

    def test_airbrakes_update(self, monkeypatch, random_data_mock_imu, servo, logger, data_processor, apogee_predictor):
        """Tests whether the Airbrakes update method works correctly by calling the relevant methods.

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

        def log(self, state, extension, imu_data_packets, processed_data_packets, apogee):
            # monkeypatched method of Logger
            calls.append("log called")
            asserts.append(len(imu_data_packets) > 10)
            asserts.append(state == "CoastState")
            asserts.append(extension == ServoExtension.MIN_EXTENSION.value)
            asserts.append(imu_data_packets[0].timestamp == pytest.approx(time.time(), rel=1e9))
            asserts.append(processed_data_packets[0].current_altitude == 0.0)
            asserts.append(apogee == 0.0)

        def apogee_update(self, processed_data_packets):
            calls.append("apogee update called")

        mocked_airbrakes = AirbrakesContext(servo, random_data_mock_imu, logger, data_processor, apogee_predictor)
        mocked_airbrakes.state = CoastState(mocked_airbrakes)  # Set to coast state to test apogee update
        mocked_airbrakes.start()

        time.sleep(0.01)  # Sleep a bit so that the IMU queue is being filled

        assert mocked_airbrakes.imu._data_queue.qsize() > 0
        assert mocked_airbrakes.state.name == "CoastState"
        assert mocked_airbrakes.data_processor._last_data_packet is None

        monkeypatch.setattr(data_processor.__class__, "update", data_processor_update)
        monkeypatch.setattr(apogee_predictor.__class__, "update", apogee_update)
        monkeypatch.setattr(mocked_airbrakes.state.__class__, "update", state)
        monkeypatch.setattr(logger.__class__, "log", log)

        # Let's call .update() and check if stuff was called and/or changed:
        mocked_airbrakes.update()

        assert len(calls) == 4
        assert calls == ["update called", "state update called", "apogee update called", "log called"]
        assert all(asserts)

        mocked_airbrakes.stop()
