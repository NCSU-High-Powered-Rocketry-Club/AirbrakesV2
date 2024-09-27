import time
from abc import ABC

import pytest

from airbrakes.state import CoastState, FreeFallState, LandedState, MotorBurnState, StandByState, State
from constants import SERVO_DELAY, ServoExtension


@pytest.fixture
def state(airbrakes):
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
def flight_state(airbrakes):
    f = CoastState(airbrakes)
    f.context.state = f
    return f


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
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        time.sleep(SERVO_DELAY + 0.2)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ
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
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        time.sleep(SERVO_DELAY + 0.2)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ
        assert issubclass(stand_by_state.__class__, State)

    def test_name(self, stand_by_state):
        assert stand_by_state.name == "StandByState"

    @pytest.mark.parametrize(
        ("current_speed", "current_altitude", "expected_state"),
        [
            (0.0, 0.0, StandByState),
            (0.0, 100.0, MotorBurnState),
            (5.0, 0.3, StandByState),
            (11, 7, MotorBurnState),
            (20, 15, MotorBurnState),
        ],
        ids=["at_launchpad", "only_alt_update", "slow_alt_update", "optimal_condition", "high_speed"],
    )
    def test_update(self, stand_by_state, current_speed, current_altitude, expected_state):
        stand_by_state.context.data_processor._speed = current_speed
        stand_by_state.context.data_processor._current_altitude = current_altitude
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
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        time.sleep(SERVO_DELAY + 0.2)  # wait for servo to extend
        assert airbrakes.servo.current_extension == ServoExtension.MIN_NO_BUZZ
        assert issubclass(motor_burn_state.__class__, State)

    def test_name(self, motor_burn_state):
        assert motor_burn_state.name == "MotorBurnState"

    @pytest.mark.parametrize(
        ("current_speed", "max_speed", "expected_state", "burn_time", "airbrakes_ext"),
        [
            (0.0, 0.0, MotorBurnState, 0.0, 0.0),
            (100.0, 100.0, MotorBurnState, 0.00, 0.0),
            (50.0, 54.0, CoastState, 0.00, 1.0),
            (60.0, 60.0, CoastState, 2.4, 1.0),
        ],
        ids=["at_launchpad", "motor_burn", "decreasing_speed", "faulty_speed"],
    )
    def test_update(self, motor_burn_state, current_speed, max_speed, expected_state, burn_time, airbrakes_ext):
        motor_burn_state.context.data_processor._speed = current_speed
        motor_burn_state.context.data_processor._max_speed = max_speed
        time.sleep(burn_time)
        motor_burn_state.update()
        assert isinstance(motor_burn_state.context.state, expected_state)
        assert motor_burn_state.context.current_extension == airbrakes_ext


class TestFlightState:
    """Tests the FlightState class"""

    def test_slots(self, flight_state):
        inst = flight_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, flight_state, airbrakes):
        assert flight_state.context == airbrakes
        assert flight_state.context.current_extension == 0.0
        assert issubclass(flight_state.__class__, State)

    def test_name(self, flight_state):
        assert flight_state.name == "FlightState"

    @pytest.mark.parametrize(
        ("current_altitude", "max_altitude", "expected_state"),
        [
            (200.0, 200.0, CoastState),
            (100.0, 150.0, CoastState),
            (100.0, 400.0, FreeFallState),
        ],
        ids=["climbing", "just_descent", "apogee_threshold"],
    )
    def test_update(self, flight_state, current_altitude, max_altitude, expected_state):
        flight_state.context.data_processor._current_altitude = current_altitude
        flight_state.context.data_processor._max_altitude = max_altitude
        flight_state.update()
        assert isinstance(flight_state.context.state, expected_state)
        assert flight_state.context.current_extension == 0.0


class TestFreeFallState:
    """Tests the FreeFallState class"""

    def test_slots(self, free_fall_state):
        inst = free_fall_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, free_fall_state, airbrakes):
        assert free_fall_state.context == airbrakes
        assert free_fall_state.context.current_extension == 0.0
        assert issubclass(free_fall_state.__class__, State)

    def test_name(self, free_fall_state):
        assert free_fall_state.name == "FreeFallState"

    @pytest.mark.parametrize(
        ("current_altitude", "expected_state"),
        [
            (50.0, FreeFallState),
            (19.0, FreeFallState),
            (10.0, LandedState),
        ],
        ids=["falling", "almost_landed", "landed"],
    )
    def test_update(self, free_fall_state, current_altitude, expected_state):
        free_fall_state.context.data_processor._current_altitude = current_altitude
        free_fall_state.update()
        assert isinstance(free_fall_state.context.state, expected_state)
        assert free_fall_state.context.current_extension == 0.0


class TestLandedState:
    """Tests the LandedState class"""

    def test_slots(self, landed_state):
        inst = landed_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, landed_state, airbrakes):
        assert landed_state.context == airbrakes
        assert landed_state.context.current_extension == 0.0
        assert issubclass(landed_state.__class__, State)

    def test_name(self, landed_state):
        assert landed_state.name == "LandedState"
