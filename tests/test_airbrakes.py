import pytest

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.state import StandByState


@pytest.fixture
def airbrakes(imu, logger, servo):
    return AirbrakesContext(logger, servo, imu)


@pytest.mark.filterwarnings("ignore:To reduce servo jitter")  # ignore warning about servo jitter
class TestAirbrakesContext:
    """Tests the AirbrakesContext class"""

    def test_slots(self, airbrakes):
        inst = airbrakes
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, airbrakes, logger, imu, servo):
        assert airbrakes.logger == logger
        assert airbrakes.servo == servo
        assert airbrakes.imu == imu
        assert airbrakes.current_extension == 0.0
        assert isinstance(airbrakes.data_processor, IMUDataProcessor)
        assert isinstance(airbrakes.state, StandByState)
        assert not airbrakes.shutdown_requested

    def test_set_extension(self, airbrakes):
        # Hardcoded calculated values, based on MIN_EXTENSION and MAX_EXTENSION in constants.py
        airbrakes.set_airbrake_extension(0.5)
        # TODO: airbrakes.current_extension must be set to 0.5 !!
        assert airbrakes.servo.current_extension == 0.0803
        airbrakes.set_airbrake_extension(0.0)
        assert airbrakes.servo.current_extension == -0.0999
        airbrakes.set_airbrake_extension(1.0)
        assert airbrakes.servo.current_extension == 0.2605

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
        assert airbrakes.servo.current_extension == -0.0999  # set to "0"
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

    def test_airbrakes_update(self, monkeypatch):
        """Tests whether the Airbrakes update method works correctly."""
        # TODO: Implement this test after we get the state and apogee detection working
