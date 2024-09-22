from abc import ABC

import pytest

from airbrakes.state import FlightState, FreeFallState, MotorBurnState, StandByState, State


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
    f = FlightState(airbrakes)
    f.context.state = f
    return f


@pytest.fixture
def free_fall_state(airbrakes):
    f = FreeFallState(airbrakes)
    f.context.state = f
    return f


class TestState:
    """Tests the base State class"""

    def test_slots(self, state):
        inst = state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, state, airbrakes):
        assert state.context == airbrakes
        assert state.context.current_extension == 0.0
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
        assert stand_by_state.context.current_extension == 0.0
        assert issubclass(stand_by_state.__class__, State)

    def test_name(self, stand_by_state):
        assert stand_by_state.name == "StandByState"

    @pytest.mark.parametrize(
        ("current_speed", "current_altitude", "expected_state"),
        [
            (0.0, 0.0, StandByState),
            (0.0, 100.0, StandByState),
            (5.0, 0.3, StandByState),
            (5.0, 3, MotorBurnState),
            (6.0, 1, MotorBurnState),
        ],
        ids=["at_launchpad", "faulty_altitude", "slow_alt_update", "optimal_condition", "high_speed"],
    )
    def test_update(self, stand_by_state, current_speed, current_altitude, expected_state):
        stand_by_state.context.data_processor._speed = current_speed
        stand_by_state.context.data_processor._current_altitude = current_altitude
        stand_by_state.update()
        assert isinstance(stand_by_state.context.state, expected_state)
        assert stand_by_state.context.current_extension == 0.0


class TestMotorBurnState:
    """Tests the MotorBurnState class"""

    def test_slots(self, motor_burn_state):
        inst = motor_burn_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, motor_burn_state, airbrakes):
        assert motor_burn_state.context == airbrakes
        assert motor_burn_state.context.current_extension == 0.0
        assert issubclass(motor_burn_state.__class__, State)

    def test_name(self, motor_burn_state):
        assert motor_burn_state.name == "MotorBurnState"

    @pytest.mark.parametrize(
        ("avg_acceleration_mag", "current_speed", "max_speed", "expected_state"),
        [
            (0.0, 0.0, 0.0, MotorBurnState),
            (0.0, 100.0, 100.0, FlightState),
            (5.0, 50.0, 54.0, FlightState),
            (7.0, 89.0, 89.0, MotorBurnState),
            (6.0, 60.0, 60.0, FlightState),
        ],
        ids=["at_launchpad", "faulty_speed", "decreasing_speed", "still_burning", "threshold"],
    )
    def test_update(self, motor_burn_state, avg_acceleration_mag, current_speed, max_speed, expected_state):
        motor_burn_state.context.data_processor._avg_accel_mag = avg_acceleration_mag
        motor_burn_state.context.data_processor._speed = current_speed
        motor_burn_state.context.data_processor._max_speed = max_speed
        motor_burn_state.update()
        assert isinstance(motor_burn_state.context.state, expected_state)
        assert motor_burn_state.context.current_extension == 0.0


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
        ("current_speed", "current_altitude", "max_altitude", "expected_state"),
        [
            (20.0, 100.0, 100.0, FlightState),
            (10.0, 100.0, 100.0, FreeFallState),
            (13.0, 90.0, 100.0, FreeFallState),
            (5.0, 80.0, 90.0, FreeFallState),
        ],
        ids=["climbing", "threshold", "high_speed_but_falling", "low_speed_fall"],
    )
    def test_update(self, flight_state, current_speed, current_altitude, max_altitude, expected_state):
        flight_state.context.data_processor._speed = current_speed
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
