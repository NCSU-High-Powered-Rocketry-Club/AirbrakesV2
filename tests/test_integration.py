"""Tests the full integration of the airbrakes system. This is done by reading data from a previous launch and manually
verifying the data output by the code. This test will run at full speed in the CI. To run it in real time,
see `main.py` or instructions in the `README.md`."""

import csv
import time

import msgspec
import pytest

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.data_handling.logged_data_packet import LoggedDataPacket
from constants import ServoExtension, StateSettings

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

    # general method of testing this is capturing the state of the system at different points in time and verifying
    # that the state is as expected at each point in time.
    def test_update(self, logger, mock_imu, data_processor, servo):
        """Tests whether the whole system works, i.e. state changes, correct logged data, etc."""
        # We will be inspecting the state of the system at different points in time.
        # The state of the system is given as a dictionary, with the keys being the "State",
        # values being StateInformation, which will note information about that state.
        # Example:
        # {
        # "StandByState": StateInformation(min_velocity=0.0, max_velocity=0.0,
        #           extensions=[0.0, ...], min_altitude=0.0, max_altitude=0.0),
        #  ...
        # }
        states_dict: dict[str, StateInformation] = {}

        ab = AirbrakesContext(servo, mock_imu, logger, data_processor)

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

                # During the first snapshot of a state, we set the min values to the current values
                if state_info.min_velocity is None:
                    state_info.min_velocity = ab.data_processor.vertical_velocity
                    state_info.max_velocity = ab.data_processor.vertical_velocity
                    state_info.max_altitude = ab.data_processor.current_altitude
                    state_info.min_altitude = ab.data_processor.current_altitude
                    state_info.apogee_prediction = ab.apogee_predictor.apogee

                state_info.min_velocity = min(ab.data_processor.vertical_velocity, state_info.min_velocity)
                state_info.min_altitude = min(ab.data_processor.current_altitude, state_info.min_altitude)
                state_info.extensions.append(ab.current_extension)
                state_info.max_velocity = max(ab.data_processor.vertical_velocity, state_info.max_velocity)
                state_info.max_altitude = max(ab.data_processor.current_altitude, state_info.max_altitude)
                state_info.apogee_prediction.append(ab.apogee_predictor.apogee)

                # Update the state information in the dictionary
                states_dict[ab.state.name] = state_info

                # Reset the snapshot timer
                snap_start_timer = time.time()

        # Stop the airbrakes system after the data is exhausted from the csv file:
        ab.stop()

        # Let's validate our data!

        # Check we have all the states:
        assert len(states_dict) == 5
        # Order of states matters!
        assert list(states_dict.keys()) == [
            "StandByState",
            "MotorBurnState",
            "CoastState",
            "FreeFallState",
            "LandedState",
        ]

        # Now let's check if the values in each state are as expected:
        assert states_dict["StandByState"].min_velocity == pytest.approx(0.0, abs=0.1)
        assert states_dict["StandByState"].max_velocity <= StateSettings.TAKEOFF_VELOCITY
        assert states_dict["StandByState"].min_altitude >= -6.0  # might be negative due to noise/flakiness
        assert states_dict["StandByState"].max_altitude <= StateSettings.TAKEOFF_HEIGHT
        assert not states_dict["StandByState"].apogee_prediction
        assert all(ext == ServoExtension.MIN_EXTENSION.value for ext in states_dict["StandByState"].extensions)

        assert states_dict["MotorBurnState"].min_velocity >= StateSettings.TAKEOFF_VELOCITY
        assert states_dict["MotorBurnState"].max_velocity <= 300.0  # arbitrary value, we haven't hit Mach 1
        assert states_dict["MotorBurnState"].min_altitude >= -2.5  # detecting takeoff from velocity data
        assert states_dict["MotorBurnState"].max_altitude >= StateSettings.TAKEOFF_HEIGHT
        assert states_dict["MotorBurnState"].max_altitude <= 500.0  # Our motor burn time isn't usually that long
        assert not states_dict["MotorBurnState"].apogee_prediction
        assert all(ext == ServoExtension.MIN_EXTENSION.value for ext in states_dict["MotorBurnState"].extensions)

        # TODO: Fix our current velocity (kalman filter). Currently tests with broken velocity values:
        # our coasting velocity be fractionally higher than motor burn velocity due to data processing time
        # (does not actually happen in real life)
        assert (states_dict["CoastState"].max_velocity - 10) <= states_dict["MotorBurnState"].max_velocity
        assert states_dict["CoastState"].min_velocity <= 50.0  # velocity around apogee should be low
        assert states_dict["CoastState"].min_altitude >= states_dict["MotorBurnState"].max_altitude
        assert states_dict["CoastState"].max_altitude <= 2000.0  # arbitrary value
        apogee_pred_list = states_dict["CoastState"].apogee_prediction
        medianPrediction = sum(apogee_pred_list) / len(apogee_pred_list)
        max_apogee = states_dict["CoastState"].max_altitude
        assert max_apogee * 0.9 <= medianPrediction <= max_apogee * 1.1

        # Check if we have extended the airbrakes at least once
        # specially on subscale flights, where coast phase is very short anyway.
        # We should hit target apogee, and then deploy airbrakes:
        assert any(ext == ServoExtension.MAX_EXTENSION.value for ext in states_dict["CoastState"].extensions)

        assert states_dict["FreeFallState"].min_velocity >= 7.0  # velocity might be less than gravity (parachutes)
        assert states_dict["FreeFallState"].max_velocity <= 300.0  # high error for now
        # max altitude should be less than coasting altitude minus some error
        assert (
            states_dict["CoastState"].max_altitude - states_dict["FreeFallState"].max_altitude
            >= StateSettings.DISTANCE_FROM_APOGEE - 10
        )

        assert (
            states_dict["FreeFallState"].min_altitude <= StateSettings.GROUND_ALTITUDE + 10.0
        )  # free fall should be close to ground
        assert all(ext == ServoExtension.MIN_EXTENSION.value for ext in states_dict["FreeFallState"].extensions)

        # TODO: update after fixing velocity calculations:
        # assert states_dict["LandedState"].min_velocity == 0.0
        assert states_dict["LandedState"].max_velocity <= 300.0  # high error for now
        assert states_dict["LandedState"].min_altitude <= StateSettings.GROUND_ALTITUDE
        assert states_dict["LandedState"].max_altitude <= StateSettings.GROUND_ALTITUDE + 10.0
        assert all(ext == ServoExtension.MIN_EXTENSION.value for ext in states_dict["LandedState"].extensions)

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

                # Check if we logged velocity and zeroed out alt for estimated data packets:
                if is_est_data_packet:
                    assert row["velocity"] != ""
                    assert row["current_altitude"] != ""

                # Check if the extension is a float:
                assert float(extension) in [ServoExtension.MIN_EXTENSION.value, ServoExtension.MAX_EXTENSION.value]

            # Check if we have a lot of lines in the log file:
            assert line_number > 80_000  # arbitrary value, depends on length of log buffer and flight data.

            # Check if all states were logged:
            assert state_list == ["S", "M", "C", "F", "L"]
