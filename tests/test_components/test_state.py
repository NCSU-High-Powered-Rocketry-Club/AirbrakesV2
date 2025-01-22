from abc import ABC

import pytest

from airbrakes.constants import (
    GROUND_ALTITUDE_METERS,
    LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED,
    LOG_BUFFER_SIZE,
    MAX_FREE_FALL_SECONDS,
    MAX_VELOCITY_THRESHOLD,
    ServoExtension,
)
from airbrakes.state import (
    CoastState,
    FreeFallState,
    LandedState,
    MotorBurnState,
    StandbyState,
    State,
)
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket
from tests.auxil.utils import make_apogee_predictor_data_packet


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
def standby_state(airbrakes):
    return StandbyState(airbrakes)


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
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        assert issubclass(state.__class__, ABC)

    def test_name(self, state):
        assert state.name == "StateImpl"


class TestStandbyState:
    """Tests the StandbyState class"""

    def test_slots(self, standby_state):
        inst = standby_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, standby_state, airbrakes):
        assert standby_state.context == airbrakes
        assert issubclass(standby_state.__class__, State)

    def test_name(self, standby_state):
        assert standby_state.name == "StandbyState"

    @pytest.mark.parametrize(
        ("current_velocity", "expected_state"),
        [
            (0.0, StandbyState),
            (5.0, StandbyState),
            (30, MotorBurnState),
        ],
        ids=[
            "at_launchpad",
            "slow_acc_update",
            "high_velocity",
        ],
    )
    def test_update(self, standby_state, current_velocity, expected_state):
        standby_state.context.data_processor._vertical_velocities = [current_velocity]
        standby_state.update()
        assert isinstance(standby_state.context.state, expected_state)


class TestMotorBurnState:
    """Tests the MotorBurnState class"""

    def test_slots(self, motor_burn_state):
        inst = motor_burn_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, motor_burn_state, airbrakes):
        assert motor_burn_state.context == airbrakes
        assert issubclass(motor_burn_state.__class__, State)
        assert motor_burn_state.start_time_ns == 0

    def test_camera_recording_started(self, airbrakes):
        """Tests that the camera recording is started when the motor burn starts."""

        assert airbrakes.camera.motor_burn_started.is_set() is False

        m = MotorBurnState(airbrakes)
        m.context.state = m

        assert airbrakes.camera.motor_burn_started.is_set() is True

    def test_name(self, motor_burn_state):
        assert motor_burn_state.name == "MotorBurnState"

    @pytest.mark.parametrize(
        (
            "current_velocity",
            "max_velocity",
            "expected_state",
        ),
        [
            (0.0, 0.0, MotorBurnState),
            (100.0, 100.0, MotorBurnState),
            (53.9, 54.0, MotorBurnState),  # tests that we don't switch states too early
            (
                53.999 - 54.0 * MAX_VELOCITY_THRESHOLD,
                54.0,
                CoastState,
            ),  # tests that the threshold works
        ],
        ids=[
            "at_launchpad",
            "motor_burn",
            "decreasing_velocity_under_threshold",
            "decreasing_velocity_over_threshold",
        ],
    )
    def test_update(self, motor_burn_state, current_velocity, max_velocity, expected_state):
        motor_burn_state.context.data_processor._vertical_velocities = [current_velocity]
        motor_burn_state.context.data_processor._max_vertical_velocity = max_velocity
        motor_burn_state.context.data_processor._last_data_packet = EstimatedDataPacket(1.0 * 1e9)
        motor_burn_state.update()
        assert isinstance(motor_burn_state.context.state, expected_state)
        assert motor_burn_state.context.servo.current_extension == ServoExtension.MIN_EXTENSION


class TestCoastState:
    """Tests the CoastState class"""

    def test_slots(self, coast_state):
        inst = coast_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, coast_state, airbrakes):
        assert coast_state.context == airbrakes
        assert coast_state.context.servo.current_extension == ServoExtension.MIN_EXTENSION
        assert issubclass(coast_state.__class__, State)

    def test_name(self, coast_state):
        assert coast_state.name == "CoastState"

    @pytest.mark.parametrize(
        (
            "current_altitude",
            "max_altitude",
            "vertical_velocity",
            "predicted_apogee",
            "expected_state",
            "airbrakes_ext",
        ),
        [
            (200.0, 200.0, 100.0, 300.0, CoastState, ServoExtension.MIN_EXTENSION),
            (100.0, 150.0, -20.0, 151.0, FreeFallState, ServoExtension.MIN_EXTENSION),
            (100.0, 400.0, 140.1, 5000.1, FreeFallState, ServoExtension.MIN_EXTENSION),
            (200.1, 200.1, 0.0, 200.1, FreeFallState, ServoExtension.MIN_EXTENSION),
        ],
        ids=[
            "climbing",
            "just_descent",
            "faulty_speed",
            "at_apogee",
        ],
    )
    def test_update_without_controls(
        self,
        coast_state,
        current_altitude,
        max_altitude,
        vertical_velocity,
        predicted_apogee,
        expected_state,
        airbrakes_ext,
        monkeypatch,
    ):
        coast_state.context.data_processor._current_altitudes = [current_altitude]
        coast_state.context.data_processor._max_altitude = max_altitude
        coast_state.context.data_processor._vertical_velocities = [vertical_velocity]
        coast_state.context.apogee_predictor_data_packets = [
            make_apogee_predictor_data_packet(
                predicted_apogee=predicted_apogee,
            )
        ]
        # Just set the target altitude to the predicted apogee, since we are not testing the
        # controls logic in this test:
        monkeypatch.setattr("airbrakes.state.TARGET_ALTITUDE_METERS", predicted_apogee)
        coast_state.update()
        assert isinstance(coast_state.context.state, expected_state), (
            f"Got {coast_state.context.state.name}, expected {expected_state!r}"
        )
        assert coast_state.context.servo.current_extension == airbrakes_ext

    @pytest.mark.parametrize(
        (
            "target_altitude",
            "predicted_apogee",
            "expected_airbrakes",
        ),
        [
            (1100.0, 1130.2, ServoExtension.MAX_EXTENSION),
            (1152.1, 1150.1, ServoExtension.MIN_EXTENSION),
            (1168.1, 1160.1, ServoExtension.MIN_EXTENSION),
            (1170.1, 1170.1, ServoExtension.MIN_EXTENSION),
            (1189.4, 1190.1, ServoExtension.MAX_EXTENSION),
            (1191.9, 1200.5, ServoExtension.MAX_EXTENSION),
        ],
        ids=[
            "extend_1",
            "retract_1",
            "retract_2",
            "equal_alt",
            "extend_2",
            "extend_3",
        ],
    )
    def test_update_with_controls(
        self, coast_state, monkeypatch, target_altitude, predicted_apogee, expected_airbrakes
    ):
        coast_state.context.last_apogee_predictor_packet = make_apogee_predictor_data_packet(
            predicted_apogee=predicted_apogee,
        )

        # set a dummy value to prevent state changes:
        monkeypatch.setattr(coast_state.__class__, "next_state", lambda _: None)
        monkeypatch.setattr("airbrakes.state.TARGET_ALTITUDE_METERS", target_altitude)
        coast_state.update()
        assert coast_state.context.servo.current_extension == expected_airbrakes

    def test_update_control_only_once(self, coast_state, monkeypatch):
        """Check that we only tell the airbrakes to extend once, and not send the command
        repeatedly."""
        calls = 0

        def extend_airbrakes(_):
            nonlocal calls
            calls += 1

        # patch the extend_airbrakes method to count the number of calls made:
        monkeypatch.setattr(coast_state.context.__class__, "extend_airbrakes", extend_airbrakes)

        monkeypatch.setattr("airbrakes.state.TARGET_ALTITUDE_METERS", 900.0)
        coast_state.context.last_apogee_predictor_packet = make_apogee_predictor_data_packet(
            predicted_apogee=1000.0,
        )

        coast_state.update()
        assert calls == 1
        coast_state.update()
        assert calls == 1

    def test_update_no_apogee_available_no_controls(self, coast_state):
        """Check that if we don't have an apogee prediction, we don't extend the airbrakes."""
        assert not coast_state.context.last_apogee_predictor_packet.predicted_apogee
        coast_state.update()
        assert coast_state.context.servo.current_extension == ServoExtension.MIN_EXTENSION

    def test_update_retract_airbrakes_from_extended(self, coast_state, monkeypatch):
        """Check that if we are extended, and the predicted apogee is less than the target altitude,
        we retract the airbrakes."""
        # set a dummy value to prevent state changes:
        monkeypatch.setattr(coast_state.__class__, "next_state", lambda _: None)
        monkeypatch.setattr("airbrakes.state.TARGET_ALTITUDE_METERS", 1000.0)

        # set the airbrakes to be extended:
        coast_state.context.last_apogee_predictor_packet = make_apogee_predictor_data_packet(
            predicted_apogee=1100.0,
        )
        coast_state.update()
        assert coast_state.airbrakes_extended
        assert coast_state.context.servo.current_extension == ServoExtension.MAX_EXTENSION

        # set the predicted apogee to be less than the target altitude, to test that we retract the
        # airbrakes:
        coast_state.context.last_apogee_predictor_packet = make_apogee_predictor_data_packet(
            predicted_apogee=900.0,
        )

        coast_state.update()
        assert not coast_state.airbrakes_extended
        assert coast_state.context.servo.current_extension == ServoExtension.MIN_EXTENSION


class TestFreeFallState:
    """Tests the FreeFallState class"""

    def test_slots(self, free_fall_state):
        inst = free_fall_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, free_fall_state, airbrakes):
        assert free_fall_state.context == airbrakes
        assert free_fall_state.context.servo.current_extension == ServoExtension.MIN_EXTENSION
        assert issubclass(free_fall_state.__class__, State)

    def test_name(self, free_fall_state):
        assert free_fall_state.name == "FreeFallState"

    @pytest.mark.parametrize(
        ("current_altitude", "vertical_accel", "expected_state", "time_length"),
        [
            (
                GROUND_ALTITUDE_METERS * 4,
                LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED / 4,
                FreeFallState,
                1.0,
            ),
            (
                GROUND_ALTITUDE_METERS * 2,
                LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED / 2,
                FreeFallState,
                1.0,
            ),
            (
                GROUND_ALTITUDE_METERS - 5,
                LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED / 2,
                FreeFallState,
                1.0,
            ),
            (
                GROUND_ALTITUDE_METERS - 5,
                LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED,
                LandedState,
                1.0,
            ),
            (
                GROUND_ALTITUDE_METERS * 4,
                LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED / 4,
                FreeFallState,
                MAX_FREE_FALL_SECONDS - 1.0,
            ),
            (
                GROUND_ALTITUDE_METERS * 4,
                LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED * 4,
                LandedState,
                MAX_FREE_FALL_SECONDS,
            ),
        ],
        ids=[
            "falling",
            "almost_landed",
            "close_to_ground_but_falling",
            "landed",
            "slightly_short",
            "too_long",
        ],
    )
    def test_update(
        self,
        free_fall_state,
        current_altitude,
        vertical_accel,
        expected_state,
        time_length,
    ):
        free_fall_state.context.data_processor._current_altitudes = [current_altitude]
        free_fall_state.context.data_processor._rotated_accelerations = [vertical_accel]
        free_fall_state.start_time_ns = 0
        free_fall_state.context.data_processor._last_data_packet = EstimatedDataPacket(
            time_length * 1e9
        )
        free_fall_state.update()
        assert isinstance(free_fall_state.context.state, expected_state)
        assert free_fall_state.context.servo.current_extension == ServoExtension.MIN_EXTENSION


class TestLandedState:
    """Tests the LandedState class"""

    def test_slots(self, landed_state):
        inst = landed_state
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, landed_state, airbrakes):
        assert landed_state.context == airbrakes
        assert landed_state.context.servo.current_extension == ServoExtension.MIN_EXTENSION
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
        airbrakes.logger._log_buffer.extend([1] * LOG_BUFFER_SIZE)
        assert airbrakes.logger.is_log_buffer_full
        landed_state.update()
        assert airbrakes.shutdown_requested
        assert not airbrakes.logger.is_running
        assert not airbrakes.imu.is_running
        assert airbrakes.servo.current_extension == ServoExtension.MIN_EXTENSION
        assert not airbrakes.logger.is_log_buffer_full
        assert len(airbrakes.logger._log_buffer) == 0

    def test_next_state_does_nothing(self, landed_state):
        landed_state.next_state()
        assert landed_state.context.state == landed_state
