"""
Tests the full integration of the airbrakes system.

This is done by reading data from a previous
launch and manually verifying the data output by the code. This test will run at full speed in the
CI. To run it in real time, see `main.py` or instructions in the `README.md`.
"""

import threading
import time

import polars as pl
import pytest

from airbrakes.constants import (
    ServoExtension,
)
from airbrakes.telemetry.packets.logger_data_packet import LoggerDataPacket
from tests.auxil.launch_cases import (
    GenesisLaunchCase,
    LegacyLaunchCase,
    PelicanatorLaunchCase1,
    PelicanatorLaunchCase2,
    PelicanatorLaunchCase4,
    PurpleLaunchCase,
    ShakeNBakeLaunchCase,
    StateInformation,
)

SNAPSHOT_INTERVAL = 0.001  # seconds


class TestIntegration:
    """
    Tests the full integration of the airbrakes system by using previous launch data.
    """

    # general method of testing this is capturing the state of the system at different points in
    # time and verifying that the state is as expected at each point in time.
    def test_update(
        self,
        request,
        target_altitude,
        mock_imu_airbrakes,
        monkeypatch,
    ):
        """
        Tests whether the whole system works, i.e. state changes, correct logged data, etc.
        """
        # We will be inspecting the state of the system at different points in time.
        # The state of the system is given as a dictionary, with the keys being the "State",
        # values being StateInformation, which will note information about that state.
        # Example:
        # {
        # "StandbyState": StateInformation(min_velocity=0.0, max_velocity=0.0,
        #           extensions=[0.0, ...], min_altitude=0.0, max_altitude=0.0),
        #  ...
        # }

        # request.node.name is the name of the test function, e.g. test_update[shake_n_bake]
        launch_name = request.node.name.split("[")[-1].strip("]")

        if launch_name == "purple_launch":
            launch_case = PurpleLaunchCase
        elif launch_name == "legacy_launch_1":
            launch_case = LegacyLaunchCase
        elif launch_name == "genesis_launch_2":
            launch_case = GenesisLaunchCase
        elif launch_name == "shake_n_bake":
            launch_case = ShakeNBakeLaunchCase
        elif launch_name == "pelicanator_launch_1":
            launch_case = PelicanatorLaunchCase1
        elif launch_name == "pelicanator_launch_2":
            launch_case = PelicanatorLaunchCase2
        elif launch_name == "pelicanator_launch_4":
            launch_case = PelicanatorLaunchCase4
        else:
            raise ValueError(f"Unknown launch name: {launch_name}")

        # Since TARGET_APOGEE_METERS is bound locally to the importing module, we have to patch it
        # here. Simply doing constants.TARGET_APOGEE_METERS = target_altitude will only change it
        # here, and not in the actual state module.

        monkeypatch.setattr("airbrakes.state.TARGET_APOGEE_METERS", target_altitude)

        states_dict: dict[str, StateInformation] = {}

        ab = mock_imu_airbrakes

        # Start testing!
        snap_start_timer = ab.data_processor.current_timestamp
        ab.start(wait_for_start=True)

        # Run until the patched method in our IMU has finished (i.e. the data is exhausted)
        while ab.imu._data_fetch_process.is_alive():
            ab.update()
            if ab.data_processor.current_timestamp - snap_start_timer >= SNAPSHOT_INTERVAL:
                if ab.state.name not in states_dict:
                    # Reset the current state velocities and altitudes
                    states_dict[ab.state.name] = StateInformation(
                        extensions=[ab.servo.current_extension]
                    )

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
                    state_info.apogee_prediction.append(
                        ab.most_recent_apogee_predictor_packet.predicted_apogee
                    )

                state_info.min_velocity = min(
                    ab.data_processor.vertical_velocity, state_info.min_velocity
                )
                state_info.min_altitude = min(
                    ab.data_processor.current_altitude, state_info.min_altitude
                )
                state_info.extensions.append(ab.servo.current_extension)
                state_info.max_velocity = max(
                    ab.data_processor.vertical_velocity, state_info.max_velocity
                )
                state_info.max_altitude = max(
                    ab.data_processor.current_altitude, state_info.max_altitude
                )
                state_info.max_avg_vertical_acceleration = max(
                    ab.data_processor.average_vertical_acceleration,
                    state_info.max_avg_vertical_acceleration,
                )
                state_info.min_avg_vertical_acceleration = min(
                    ab.data_processor.average_vertical_acceleration,
                    state_info.min_avg_vertical_acceleration,
                )

                state_info.apogee_prediction.append(
                    ab.most_recent_apogee_predictor_packet.predicted_apogee
                )

                # Update the state information in the dictionary
                states_dict[ab.state.name] = state_info

                # Reset the snapshot timer
                snap_start_timer = ab.data_processor.current_timestamp

        # Stop the airbrakes system after the data is exhausted from the csv file:
        ab.stop()

        # Let's validate our data!
        launch_case_init = launch_case(states_dict, target_altitude)

        all_states = launch_case_init.all_states_present()
        assert all_states.passed, f"Test failed for {launch_name}"

        standby_cases = launch_case_init.standby_case_test()
        assert standby_cases.passed, f"Test failed for {launch_name}"

        motor_burn_cases = launch_case_init.motor_burn_case_test()
        assert motor_burn_cases.passed, f"Test failed for {launch_name}"

        coast_cases = launch_case_init.coast_case_test()
        assert coast_cases.passed, f"Test failed for {launch_name}"

        free_fall_cases = launch_case_init.free_fall_case_test()
        assert free_fall_cases.passed, f"Test failed for {launch_name}"

        landed_cases = launch_case_init.landed_case_test()
        assert landed_cases.passed, f"Test failed for {launch_name}"

        # Now let's check if everything was logged correctly using polars

        # Read the log file into a polars DataFrame
        df = pl.read_csv(ab.logger.log_path)

        # Check if all headers were logged
        assert list(df.columns) == list(LoggerDataPacket.__struct_fields__)

        # Test the first row for specific validations
        first_row = df.row(0, named=True)

        # Check if values are rounded to 8 decimal places
        accel = (
            first_row["estLinearAccelX"]
            if first_row["estLinearAccelX"] is not None
            else first_row["scaledAccelX"]
        )
        accel_str = str(accel)
        assert accel_str.count(".") == 1
        assert len(accel_str.split(".")[1]) == 8

        # Check if the timestamp is valid and in nanoseconds
        timestamp = str(first_row["timestamp"])
        assert timestamp.isdigit()
        assert int(timestamp) > 1e9

        # Check if the state field has only a single letter
        state = first_row["state_letter"]
        assert len(state) == 1

        # Get counts and perform other validations without looping
        line_number = df.height
        state_list = (
            df.group_by("state_letter", maintain_order=True)
            .agg()
            .get_column("state_letter")
            .to_list()
        )

        # Filter for coast state data
        coast_df = df.filter(pl.col("state_letter") == "C")
        pred_apogees_in_coast = (
            coast_df.filter(pl.col("predicted_apogee").is_not_null())
            .get_column("predicted_apogee")
            .to_list()
        )
        uncertainities_in_coast = (
            coast_df.filter(pl.col("uncertainty_threshold_1").is_not_null())
            .get_column("uncertainty_threshold_1")
            .to_list()
        )

        # Check estimated data packet validations
        est_data_df = df.filter(pl.col("estLinearAccelX").is_not_null())
        assert est_data_df.select(pl.col("vertical_velocity").is_not_null()).to_series().all()
        assert est_data_df.select(pl.col("current_altitude").is_not_null()).to_series().all()
        assert est_data_df.select(pl.col("vertical_acceleration").is_not_null()).to_series().all()

        # Check if extensions are valid floats
        valid_extensions = [
            ServoExtension.MIN_EXTENSION.value,
            ServoExtension.MAX_EXTENSION.value,
            ServoExtension.MIN_NO_BUZZ.value,
            ServoExtension.MAX_NO_BUZZ.value,
        ]
        all_extensions_valid = (
            df.select(pl.col("set_extension").cast(pl.Float64).is_in(valid_extensions))
            .to_series()
            .all()
        )
        assert all_extensions_valid

        # Check if we have a lot of lines in the log file
        assert launch_case_init.log_file_lines_test(line_number)

        # Predicted apogees and uncertainties should be logged in CoastState
        assert len(pred_apogees_in_coast) > 0
        assert len(uncertainities_in_coast) > 0
        assert len(uncertainities_in_coast) >= len(pred_apogees_in_coast)

        # Check if all states were logged
        assert launch_case_init.log_file_states_logged(state_list)

    @pytest.mark.imu_benchmark
    def test_fetched_imu_packets_integration(self, context):
        """
        Test that the fetched IMU packets are a reasonable size.

        Run with sudo. E.g. $ sudo -E $(which pytest) tests/test_integration.py -m imu_benchmark
        """
        ab = context

        TEST_TIME_SECONDS = 15  # Amount of time to keep testing

        # List to store all the fetched_packets from the imu
        imu_packets_per_cycle_list = []

        has_airbrakes_stopped = threading.Event()

        def stop_thread():
            """
            Stops airbrakes after a set amount of time.
            """
            ab.stop()
            has_airbrakes_stopped.set()

        t = threading.Timer(TEST_TIME_SECONDS, stop_thread)
        start_time = time.time()
        t.start()
        ab.start()

        while not context.shutdown_requested:
            context.update()

            if time.time() - start_time >= SNAPSHOT_INTERVAL:
                imu_packets_per_cycle_list.append(ab.imu.imu_packets_per_cycle)
                start_time = time.time()

        # Wait for the airbrakes to stop.
        has_airbrakes_stopped.wait(TEST_TIME_SECONDS)
        t.join()
        assert not context.imu.is_running
        assert not context.logger.is_running
        assert not context.apogee_predictor.is_running
        assert not context.imu._running.value
        assert not context.imu._data_fetch_process.is_alive()
        assert not context.logger._log_process.is_alive()
        assert not context.apogee_predictor._prediction_process.is_alive()
        assert sum(imu_packets_per_cycle_list) / len(imu_packets_per_cycle_list) <= 10
