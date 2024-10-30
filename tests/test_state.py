import time
from abc import ABC

import pytest

from airbrakes.state import CoastState, FreeFallState, LandedState, MotorBurnState, StandByState, State
from constants import ServoExtension, StateSettings


@pytest.fixture
def state(airbrakes):
    """Dummy state class to test the base State class"""

    class StateImpl(State):
        __slots__ = ()

        def update(self):
            pass

        def next_state(self):
            pass

    return StateImpl(airbrakes)


@pytest.fixture
def stand_by_state(airbrakes):
    return StandByState(airbrakes)


@pytest.fixture
def motor_burn_state(airbrakes):
    m = MotorBurnState(airbrakes)
    m.context.state = m
    return m


@pytest.fixture
def coast_state(airbrakes):
    c = CoastState(airbrakes)
    c.context.state = c
    return c


@pytest.fixture
def free_fall_state(airbrakes):
    f = FreeFallState(airbrakes)
    f.context.state = f
    return f


@pytest.fixture
def landed_state(airbrakes):
    ls = LandedState(airbrakes)
    ls.context.state = ls
    return ls


class TestState:
    """Tests the base State class"""

    def test_slots(self, state):
        inst = state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, state, airbrakes):
        assert state.context == airbrakes
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION.value
        time.sleep(StateSettings.SERVO_DELAY.value + 0.2)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ.value
        assert issubclass(state.__class__, ABC)

    def test_name(self, state):
        assert state.name == "StateImpl"


class TestStandByState:
    """Tests the StandByState class"""

    def test_slots(self, stand_by_state):
        inst = stand_by_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, stand_by_state, airbrakes):
        assert stand_by_state.context == airbrakes
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION.value
        time.sleep(StateSettings.SERVO_DELAY.value + 0.2)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ.value
        assert issubclass(stand_by_state.__class__, State)

    def test_name(self, stand_by_state):
        assert stand_by_state.name == "StandByState"

    @pytest.mark.parametrize(
        ("current_velocity", "current_altitude", "expected_state"),
        [
            (0.0, 0.0, StandByState),
            (0.0, 100.0, MotorBurnState),
            (5.0, 0.3, StandByState),
            (11, 7, MotorBurnState),
            (20, 15, MotorBurnState),
        ],
        ids=["at_launchpad", "only_alt_update", "slow_alt_update", "optimal_condition", "high_velocity"],
    )
    def test_update(self, stand_by_state, current_velocity, current_altitude, expected_state):
        stand_by_state.context.data_processor._vertical_velocities = [current_velocity]
        stand_by_state.context.data_processor._current_altitudes = [current_altitude]
        stand_by_state.update()
        assert isinstance(stand_by_state.context.state, expected_state)


class TestMotorBurnState:
    """Tests the MotorBurnState class"""

    def test_slots(self, motor_burn_state):
        inst = motor_burn_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, motor_burn_state, airbrakes):
        assert motor_burn_state.context == airbrakes
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION.value
        time.sleep(StateSettings.SERVO_DELAY.value + 0.1)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ.value
        assert issubclass(motor_burn_state.__class__, State)

    def test_name(self, motor_burn_state):
        assert motor_burn_state.name == "MotorBurnState"

    @pytest.mark.parametrize(
        ("current_velocity", "max_velocity", "expected_state", "burn_time"),
        [
            (0.0, 0.0, MotorBurnState, 0.0),
            (100.0, 100.0, MotorBurnState, 0.00),
            (53.9, 54.0, MotorBurnState, 0.00),  # tests that we don't switch states too early
            (
                53.999 - 54.0 * StateSettings.MAX_VELOCITY_THRESHOLD,
                54.0,
                CoastState,
                0.00,
            ),  # tests that the threshold works
            (60.0, 60.0, CoastState, StateSettings.MOTOR_BURN_TIME + 0.1),
        ],
        ids=[
            "at_launchpad",
            "motor_burn",
            "decreasing_velocity_under_threshold",
            "decreasing_velocity_over_threshold",
            "faulty_velocity",
        ],
    )
    def test_update(self, motor_burn_state, current_velocity, max_velocity, expected_state, burn_time):
        motor_burn_state.context.data_processor._vertical_velocities = [current_velocity]
        motor_burn_state.context.data_processor._max_vertical_velocity = max_velocity
        time.sleep(burn_time)
        motor_burn_state.update()
        assert isinstance(motor_burn_state.context.state, expected_state)
        assert motor_burn_state.context.current_extension == ServoExtension.MIN_EXTENSION.value


class TestCoastState:
    """Tests the CoastState class"""

    def test_slots(self, coast_state):
        inst = coast_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, coast_state, airbrakes):
        assert coast_state.context == airbrakes
        assert coast_state.context.current_extension == ServoExtension.MIN_EXTENSION.value
        assert issubclass(coast_state.__class__, State)

    def test_name(self, coast_state):
        assert coast_state.name == "CoastState"

    @pytest.mark.parametrize(
        ("current_altitude", "max_altitude", "expected_state", "coast_time", "airbrakes_ext"),
        [
            (200.0, 200.0, CoastState, 0.0, ServoExtension.MIN_EXTENSION.value),
            (100.0, 150.0, CoastState, 0.0, ServoExtension.MIN_EXTENSION.value),
            (100.0, 150.0, CoastState, StateSettings.AIRBRAKES_AFTER_COASTING + 0.01, ServoExtension.MAX_EXTENSION.value),
            (100.0, 400.0, FreeFallState, 0.0, ServoExtension.MIN_EXTENSION.value),
        ],
        ids=["climbing", "just_descent", "airbrakes_long_coast", "apogee_threshold"],
    )
    def test_update(self, coast_state, current_altitude, max_altitude, expected_state, coast_time, airbrakes_ext):
        coast_state.context.data_processor._current_altitudes = [current_altitude]
        coast_state.context.data_processor._max_altitude = max_altitude
        time.sleep(coast_time)
        coast_state.update()
        assert isinstance(coast_state.context.state, expected_state)
        assert coast_state.context.current_extension == airbrakes_ext


class TestFreeFallState:
    """Tests the FreeFallState class"""

    def test_slots(self, free_fall_state):
        inst = free_fall_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, free_fall_state, airbrakes):
        assert free_fall_state.context == airbrakes
        assert free_fall_state.context.current_extension == ServoExtension.MIN_EXTENSION.value
        assert issubclass(free_fall_state.__class__, State)

    def test_name(self, free_fall_state):
        assert free_fall_state.name == "FreeFallState"

    @pytest.mark.parametrize(
        ("current_altitude", "expected_state"),
        [
            (50.0, FreeFallState),
            (19.0, FreeFallState),
            (StateSettings.GROUND_ALTITUDE - 5, LandedState),
        ],
        ids=["falling", "almost_landed", "landed"],
    )
    def test_update(self, free_fall_state, current_altitude, expected_state):
        free_fall_state.context.data_processor._current_altitudes = [current_altitude]
        free_fall_state.update()
        assert isinstance(free_fall_state.context.state, expected_state)
        assert free_fall_state.context.current_extension == ServoExtension.MIN_EXTENSION.value


class TestLandedState:
    """Tests the LandedState class"""

    def test_slots(self, landed_state):
        inst = landed_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, landed_state, airbrakes):
        assert landed_state.context == airbrakes
        assert landed_state.context.current_extension == ServoExtension.MIN_EXTENSION.value
        assert issubclass(landed_state.__class__, State)

    def test_name(self, landed_state):
        assert landed_state.name == "LandedState"

    def test_update(self, landed_state, airbrakes):
        # Test that calling update before shutdown delay does not shut down the system:
        airbrakes.start()
        landed_state.update()
        assert airbrakes.logger.is_running
        assert airbrakes.imu.is_running
        assert not airbrakes.logger.is_log_buffer_full
        # Test that if our log buffer is full, we shut down the system:
        airbrakes.logger._log_buffer.extend([1] * StateSettings.LOG_BUFFER_SIZE.value)
        assert airbrakes.logger.is_log_buffer_full
        landed_state.update()
        assert airbrakes.shutdown_requested
        assert not airbrakes.logger.is_running
        assert not airbrakes.imu.is_running
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION.value
        assert not airbrakes.logger.is_log_buffer_full
        assert len(airbrakes.logger._log_buffer) == 0
