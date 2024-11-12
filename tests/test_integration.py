"""Tests the full integration of the airbrakes system. This is done by reading data from a previous
launch and manually verifying the data output by the code. This test will run at full speed in the
CI. To run it in real time, see `main.py` or instructions in the `README.md`."""

import csv
import statistics
import time
import types

import msgspec
import pytest

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from constants import (
    GROUND_ALTITUDE,
    LANDED_SPEED,
    TAKEOFF_HEIGHT,
    TAKEOFF_VELOCITY,
    ServoExtension,
)

SNAPSHOT_INTERVAL = 0.01  # seconds


class StateInformation(msgspec.Struct):
    """Records the values achieved by the airbrakes system in a particular state."""

    min_velocity: float | None = None
    max_velocity: float | None = None
    extensions: list[float] = []
    min_altitude: float | None = None
    max_altitude: float | None = None
    apogee_prediction: list[float] = []


class TestIntegration:
    """Tests the full integration of the airbrakes system by using previous launch data."""

    # general method of testing this is capturing the state of the system at different points in
    # time and verifying that the state is as expected at each point in time.
    def test_update(
        self,
        logger,
        mock_imu,
        data_processor,
        servo,
        apogee_predictor,
        request,
        target_altitude,
        monkeypatch,
    ):
        """Tests whether the whole system works, i.e. state changes, correct logged data, etc."""
        # We will be inspecting the state of the system at different points in time.
        # The state of the system is given as a dictionary, with the keys being the "State",
        # values being StateInformation, which will note information about that state.
        # Example:
        # {
        # "StandbyState": StateInformation(min_velocity=0.0, max_velocity=0.0,
        #           extensions=[0.0, ...], min_altitude=0.0, max_altitude=0.0),
        #  ...
        # }

        # request.node.name is the name of the test function, e.g. test_update[interest_launch]
        launch_name = request.node.name.split("[")[-1].strip("]")

        # Since TARGET_ALTITUDE is bound locally to the importing module, we have to patch it here.
        # simply doing constants.TARGET_ALTITUDE = target_altitude will only change it here, and not
        # in the actual state module.

        monkeypatch.setattr("airbrakes.state.TARGET_ALTITUDE", target_altitude)

        states_dict: dict[str, StateInformation] = {}

        ab = AirbrakesContext(servo, mock_imu, logger, data_processor, apogee_predictor)

        # Start testing!
        snap_start_timer = time.time()
        ab.start()

        # Run until the patched method in our IMU has finished (i.e. the data is exhausted)
        while ab.imu._data_fetch_process.is_alive():
            ab.update()
            if time.time() - snap_start_timer >= SNAPSHOT_INTERVAL:
                if ab.state.name not in states_dict:
                    # Reset the current state velocities and altitudes
                    states_dict[ab.state.name] = StateInformation(extensions=[ab.current_extension])

                # Let's update all our values:
                state_info = states_dict[ab.state.name]

                # During the first snapshot of a state, we set values to the current values
                if state_info.min_velocity is None:
                    state_info.min_velocity = ab.data_processor.vertical_velocity
                    state_info.max_velocity = ab.data_processor.vertical_velocity
                    state_info.max_altitude = ab.data_processor.current_altitude
                    state_info.min_altitude = ab.data_processor.current_altitude
                    state_info.apogee_prediction.append(ab.apogee_predictor.apogee)

                state_info.min_velocity = min(
                    ab.data_processor.vertical_velocity, state_info.min_velocity
                )
                state_info.min_altitude = min(
                    ab.data_processor.current_altitude, state_info.min_altitude
                )
                state_info.extensions.append(ab.current_extension)
                state_info.max_velocity = max(
                    ab.data_processor.vertical_velocity, state_info.max_velocity
                )
                state_info.max_altitude = max(
                    ab.data_processor.current_altitude, state_info.max_altitude
                )
                state_info.apogee_prediction.append(ab.apogee_predictor.apogee)

                # Update the state information in the dictionary
                states_dict[ab.state.name] = state_info

                # Reset the snapshot timer
                snap_start_timer = time.time()

        # Stop the airbrakes system after the data is exhausted from the csv file:
        ab.stop()

        # Let's validate our data!

        # Check we have all the states:
        if launch_name == "purple_launch":
            # Our Launches don't properly log/reach the LandedState, so we will ignore it for now.
            assert len(states_dict) == 4
            assert list(states_dict.keys()) == [
                "StandbyState",
                "MotorBurnState",
                "CoastState",
                "FreeFallState",
            ]
        else:
            assert len(states_dict) == 5
            # Order of states matters!
            assert list(states_dict.keys()) == [
                "StandbyState",
                "MotorBurnState",
                "CoastState",
                "FreeFallState",
                "LandedState",
            ]
        states_dict = types.SimpleNamespace(**states_dict)
        stand_by_state = states_dict.StandbyState
        motor_burn_state = states_dict.MotorBurnState
        coast_state = states_dict.CoastState
        free_fall_state = states_dict.FreeFallState

        # Now let's check if the values in each state are as expected:
        assert stand_by_state.min_velocity == pytest.approx(0.0, abs=0.1)
        assert stand_by_state.max_velocity <= TAKEOFF_VELOCITY
        assert stand_by_state.min_altitude >= -6.0  # might be negative due to noise/flakiness
        assert stand_by_state.max_altitude <= TAKEOFF_HEIGHT
        assert not any(stand_by_state.apogee_prediction)
        assert all(ext == ServoExtension.MIN_EXTENSION for ext in stand_by_state.extensions)

        assert motor_burn_state.min_velocity >= TAKEOFF_VELOCITY
        assert motor_burn_state.max_velocity <= 300.0  # arbitrary value, we haven't hit Mach 1
        assert motor_burn_state.min_altitude >= -2.5  # detecting takeoff from velocity data
        assert motor_burn_state.max_altitude >= TAKEOFF_HEIGHT
        assert motor_burn_state.max_altitude <= 500.0  # Our motor burn time isn't usually that long
        assert not any(motor_burn_state.apogee_prediction)
        assert all(ext == ServoExtension.MIN_EXTENSION for ext in motor_burn_state.extensions)

        # our coasting velocity be fractionally higher than motor burn velocity due to data
        # processing time (does not actually happen in real life)
        assert (coast_state.max_velocity - 10) <= motor_burn_state.max_velocity
        assert coast_state.min_velocity <= 5.0  # velocity around apogee should be low
        assert coast_state.min_altitude >= motor_burn_state.max_altitude
        assert coast_state.max_altitude <= target_altitude + 100
        apogee_pred_list = coast_state.apogee_prediction
        median_predicted_apogee = statistics.median(apogee_pred_list)
        max_apogee = coast_state.max_altitude
        assert max_apogee * 0.9 <= median_predicted_apogee <= max_apogee * 1.1

        # Check if we have extended the airbrakes at least once
        # specially on subscale flights, where coast phase is very short anyway.
        # We should hit target apogee, and then deploy airbrakes:
        assert any(ext == ServoExtension.MAX_EXTENSION for ext in coast_state.extensions)

        if launch_name == "purple_launch":
            # High errors for other flights, because we don't have good rotation data.
            assert free_fall_state.min_velocity <= -300.0
        else:
            # we have chute deployment, so we shouldn't go that fast
            assert free_fall_state.min_velocity >= -30.0
        assert free_fall_state.max_velocity <= 0.0
        # max altitude of both states should be about the same
        assert coast_state.max_altitude == pytest.approx(free_fall_state.max_altitude, rel=1e2)
        # free fall should be close to ground:
        assert free_fall_state.min_altitude <= GROUND_ALTITUDE + 10.0
        assert all(ext == ServoExtension.MIN_EXTENSION for ext in free_fall_state.extensions)

        if launch_name != "purple_launch":
            # Generated data for simulated landing for interest launcH:
            landed_state = states_dict.LandedState
            assert landed_state.min_velocity >= -LANDED_SPEED
            assert landed_state.max_velocity <= 0.1
            assert landed_state.min_altitude <= GROUND_ALTITUDE
            assert landed_state.max_altitude <= GROUND_ALTITUDE + 10.0
            assert all(ext == ServoExtension.MIN_EXTENSION for ext in landed_state.extensions)

        # Now let's check if everything was logged correctly:
        # some what of a duplicate of test_logger.py:

        with ab.logger.log_path.open() as f:
            reader = csv.DictReader(f)
            # Check if all headers were logged:
            headers = reader.fieldnames
            assert tuple(headers) == LoggedDataPacket.__struct_fields__

            # Let's just test the first line (excluding the headers) for a few things:
            line = next(reader)

            # Check if we round our values to 8 decimal places:
            accel: str = line["estLinearAccelX"] or line["scaledAccelX"]  # raw or est data
            assert accel.count(".") == 1
            assert len(accel.split(".")[1]) == 8

            # Check if the timestamp is a valid and in nanoseconds:
            timestamp: str = line["timestamp"]
            assert timestamp.isdigit()
            assert int(timestamp) > 1e9

            # Check if the state field has only a single letter:
            state: str = line["state"]
            assert len(state) == 1

            line_number = 0
            state_list = []
            for row in reader:
                line_number += 1
                state: str = row["state"]
                extension: str = row["extension"]
                is_est_data_packet: bool = row["estLinearAccelX"] != ""

                if state not in state_list:
                    state_list.append(state)

                # Check if we logged our main calculations for estimated data packets:
                if is_est_data_packet:
                    assert row["vertical_velocity"] != ""
                    assert row["current_altitude"] != ""
                    assert row["predicted_apogee"] != ""
                    assert row["vertical_acceleration"] != ""

                # Check if the extension is a float:
                assert float(extension) in [
                    ServoExtension.MIN_EXTENSION.value,
                    ServoExtension.MAX_EXTENSION.value,
                ]

            # Check if we have a lot of lines in the log file:
            # arbitrary value, depends on length of log buffer and flight data.
            assert line_number > 80_000

            # Check if all states were logged:
            if launch_name == "purple_launch":
                assert state_list == ["S", "M", "C", "F"]
            else:
                assert state_list == ["S", "M", "C", "F", "L"]
