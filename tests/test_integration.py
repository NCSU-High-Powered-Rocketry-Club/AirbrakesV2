"""Tests the full integration of the airbrakes system. This is done by reading data from a previous
launch and manually verifying the data output by the code. This test will run at full speed in the
CI. To run it in real time, see `main.py` or instructions in the `README.md`."""

import csv
import statistics
import types

import msgspec
import pytest

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.constants import (
    GROUND_ALTITUDE_METERS,
    LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED,
    TAKEOFF_HEIGHT_METERS,
    TAKEOFF_VELOCITY_METERS_PER_SECOND,
    ServoExtension,
)
from airbrakes.data_handling.packets.logger_data_packet import LoggerDataPacket

SNAPSHOT_INTERVAL = 0.001  # seconds


class StateInformation(msgspec.Struct):
    """Records the values achieved by the airbrakes system in a particular state."""

    min_velocity: float | None = None
    max_velocity: float | None = None
    extensions: list[ServoExtension] = []
    min_altitude: float | None = None
    max_altitude: float | None = None
    min_avg_vertical_acceleration: float | None = None
    max_avg_vertical_acceleration: float | None = None
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

        # Since TARGET_ALTITUDE_METERS is bound locally to the importing module, we have to patch it
        # here. Simply doing constants.TARGET_ALTITUDE_METERS = target_altitude will only change it
        # here, and not in the actual state module.

        monkeypatch.setattr("airbrakes.state.TARGET_ALTITUDE_METERS", target_altitude)

        states_dict: dict[str, StateInformation] = {}

        ab = AirbrakesContext(servo, mock_imu, logger, data_processor, apogee_predictor)

        # Start testing!
        snap_start_timer = ab.data_processor.current_timestamp
        ab.start()

        # Run until the patched method in our IMU has finished (i.e. the data is exhausted)
        while ab.imu._data_fetch_process.is_alive():
            ab.update()
            if ab.data_processor.current_timestamp - snap_start_timer >= SNAPSHOT_INTERVAL:
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
                    state_info.min_avg_vertical_acceleration = (
                        ab.data_processor.average_vertical_acceleration
                    )
                    state_info.max_avg_vertical_acceleration = (
                        ab.data_processor.average_vertical_acceleration
                    )
                    state_info.apogee_prediction.append(ab.predicted_apogee)

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
                state_info.min_avg_vertical_acceleration = min(
                    ab.data_processor.average_vertical_acceleration,
                    state_info.min_avg_vertical_acceleration,
                )
                state_info.max_avg_vertical_acceleration = max(
                    ab.data_processor.average_vertical_acceleration,
                    state_info.max_avg_vertical_acceleration,
                )

                state_info.apogee_prediction.append(ab.predicted_apogee)

                # Update the state information in the dictionary
                states_dict[ab.state.name] = state_info

                # Reset the snapshot timer
                snap_start_timer = ab.data_processor.current_timestamp

        # Stop the airbrakes system after the data is exhausted from the csv file:
        ab.stop()

        # Let's validate our data!

        # Check we have all the states:
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
        standby_state = states_dict.StandbyState
        motor_burn_state = states_dict.MotorBurnState
        coast_state = states_dict.CoastState
        free_fall_state = states_dict.FreeFallState

        # Now let's check if the values in each state are as expected:
        assert standby_state.min_velocity == pytest.approx(0.0, abs=0.1)
        assert standby_state.max_velocity <= TAKEOFF_VELOCITY_METERS_PER_SECOND
        assert standby_state.min_altitude >= -6.0  # might be negative due to noise/flakiness
        assert standby_state.max_altitude <= TAKEOFF_HEIGHT_METERS
        assert not any(standby_state.apogee_prediction)
        # Assert that only MIN_EXTENSION and MIN_NO_BUZZ are in the extensions list:
        assert (
            ServoExtension.MIN_EXTENSION in standby_state.extensions
            or ServoExtension.MIN_NO_BUZZ in standby_state.extensions
        )

        assert motor_burn_state.min_velocity >= TAKEOFF_VELOCITY_METERS_PER_SECOND
        assert motor_burn_state.max_avg_vertical_acceleration >= 90.0
        assert motor_burn_state.max_velocity <= 300.0  # arbitrary value, we haven't hit Mach 1
        assert motor_burn_state.min_altitude >= -2.5  # detecting takeoff from velocity data
        assert motor_burn_state.max_altitude >= TAKEOFF_HEIGHT_METERS
        assert motor_burn_state.max_altitude <= 500.0  # Our motor burn time isn't usually that long
        assert not any(motor_burn_state.apogee_prediction)
        # Assert that only MIN_EXTENSION and MIN_NO_BUZZ are in the extensions list:
        assert (
            ServoExtension.MIN_EXTENSION in motor_burn_state.extensions
            or ServoExtension.MIN_NO_BUZZ in motor_burn_state.extensions
        )

        # ------- COAST STATE -------
        # our coasting velocity be fractionally higher than motor burn velocity due to data
        # processing time (does not actually happen in real life)
        assert (coast_state.max_velocity - 15) <= motor_burn_state.max_velocity
        assert coast_state.min_velocity <= 11.0  # velocity around apogee should be low
        assert coast_state.min_altitude >= motor_burn_state.max_altitude
        assert coast_state.max_altitude <= target_altitude + 100
        apogee_pred_list = coast_state.apogee_prediction
        # Check that our apogee prediction is within 10% of the target altitude
        median_predicted_apogee = statistics.median(apogee_pred_list)
        max_apogee = coast_state.max_altitude
        assert max_apogee * 0.9 <= median_predicted_apogee <= max_apogee * 1.1

        # Check if we have extended the airbrakes at least once
        # specially on subscale flights, where coast phase is very short anyway.
        # We should hit target apogee, and then deploy airbrakes:
        assert {
            ServoExtension.MIN_EXTENSION,
            ServoExtension.MIN_NO_BUZZ,
            ServoExtension.MAX_EXTENSION,
            ServoExtension.MAX_NO_BUZZ,
        }.issuperset(set(coast_state.extensions))

        # ------- FREE FALL STATE -------
        if launch_name == "purple_launch":
            # High errors for this flight, because we don't have good rotation data.
            assert free_fall_state.min_velocity <= -300.0
        else:
            # we have chute deployment, so we shouldn't go that fast
            assert free_fall_state.min_velocity >= -30.0
        assert free_fall_state.max_velocity <= 0.0
        # max altitude of both states should be about the same
        assert coast_state.max_altitude == pytest.approx(free_fall_state.max_altitude, rel=5)
        # free fall should be close to ground:
        assert free_fall_state.min_altitude <= GROUND_ALTITUDE_METERS + 10.0
        # Assert that only MIN_EXTENSION and MIN_NO_BUZZ are in the extensions list:
        assert (
            ServoExtension.MIN_EXTENSION in free_fall_state.extensions
            or ServoExtension.MIN_NO_BUZZ in free_fall_state.extensions
        )

        # ------- LANDED STATE -------
        if launch_name != "purple_launch":
            # Generated data for simulated landing for interest launcH:
            landed_state = states_dict.LandedState
            assert (
                landed_state.max_avg_vertical_acceleration
                >= LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED
            )
            assert landed_state.max_velocity <= 0.1
            assert landed_state.min_altitude <= GROUND_ALTITUDE_METERS
            assert landed_state.max_altitude <= GROUND_ALTITUDE_METERS + 10.0
            # Assert that only MIN_EXTENSION and MIN_NO_BUZZ are in the extensions list:
            # Unfortunately, since our sim is that fast, the thread to execute MIN_NO_BUZZ doesn't
            # trigger
            assert (
                ServoExtension.MIN_EXTENSION in landed_state.extensions
                or ServoExtension.MIN_NO_BUZZ in landed_state.extensions
            )

        # Now let's check if everything was logged correctly:
        # somewhat of a duplicate of test_logger.py:

        with ab.logger.log_path.open() as f:
            reader = csv.DictReader(f)
            # Check if all headers were logged:
            headers = reader.fieldnames
            assert list(headers) == list(LoggerDataPacket.__annotations__)

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
            state: str = line["state_letter"]
            assert len(state) == 1

            line_number = 0
            batch_number = 0
            state_list = []
            pred_apogees_in_coast = []
            uncertainities_in_coast = []

            for row in reader:
                line_number += 1
                state: str = row["state_letter"]
                extension: str = row["set_extension"]
                is_est_data_packet: bool = row["estLinearAccelX"] != ""

                if state not in state_list:
                    state_list.append(state)

                # Check if we logged convergence params in CoastState:
                if state == "C":
                    if row["predicted_apogee"]:
                        pred_apogees_in_coast.append(row["predicted_apogee"])
                    if row["uncertainty_threshold_1"]:
                        uncertainities_in_coast.append(row["uncertainty_threshold_1"])
                # else:
                #     assert row["predicted_apogee"] == ""
                #     assert row["uncertainty_threshold_1"] == ""

                # Check if we logged our main calculations for estimated data packets:
                if is_est_data_packet:
                    assert row["vertical_velocity"] != ""
                    assert row["current_altitude"] != ""
                    assert row["vertical_acceleration"] != ""

                # Check if the extension is a float:
                assert float(extension) in [
                    ServoExtension.MIN_EXTENSION.value,
                    ServoExtension.MAX_EXTENSION.value,
                    ServoExtension.MIN_NO_BUZZ.value,
                    ServoExtension.MAX_NO_BUZZ.value,
                ]

                batch_number = int(row["batch_number"])

            # Check if we have a lot of lines in the log file:
            # arbitrary value, depends on length of log buffer and flight data.
            assert line_number > 80_000

            # More than 1000 iterations:
            assert batch_number > 1000

            # Predicted apogees and uncertainties should be logged in CoastState:
            assert pred_apogees_in_coast
            assert uncertainities_in_coast
            assert len(uncertainities_in_coast) >= len(pred_apogees_in_coast)

            # Check if all states were logged:
            assert state_list == ["S", "M", "C", "F", "L"]
