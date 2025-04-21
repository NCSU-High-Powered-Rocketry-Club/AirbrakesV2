"""
This module contains the test cases for the launch data.

The test cases are used in test_integration.py to test the launch data.
"""

import statistics
import types

import msgspec
import pytest

from airbrakes.constants import (
    GROUND_ALTITUDE_METERS,
    LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED,
    TAKEOFF_VELOCITY_METERS_PER_SECOND,
    ServoExtension,
)


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


class LaunchCase:
    """
    The general test cases for the launch data.

    This is the ideal case. Other launch data classes can inherit from this class and override the
    methods to test the specific launch data (e.g. failed chute deploy, data cutoffs, etc).
    """

    def __init__(self, states_dict: dict[str, StateInformation], target_apogee: float) -> None:
        self.states_dict: dict[str, StateInformation] = states_dict
        states_info = types.SimpleNamespace(**states_dict)
        self.standby_case: StateInformation | None = getattr(states_info, "StandbyState", None)
        self.motor_burn_case: StateInformation | None = getattr(states_info, "MotorBurnState", None)
        self.coast_case: StateInformation | None = getattr(states_info, "CoastState", None)
        self.free_fall_case: StateInformation | None = getattr(states_info, "FreeFallState", None)
        self.landed_case: StateInformation | None = getattr(states_info, "LandedState", None)
        self.target_apogee: float = target_apogee

    def test_all_states_present(self) -> dict[str, bool]:
        """Tests whether all states are present in the states_dict."""
        # Check we have all the states:
        test_cases = {
            "length_states_dict": False,
            "order_states_dict": False,
        }
        test_cases["length_states_dict"] = len(self.states_dict) == 5
        # Order of states matters!
        test_cases["order_states_dict"] = list(self.states_dict.keys()) == [
            "StandbyState",
            "MotorBurnState",
            "CoastState",
            "FreeFallState",
            "LandedState",
        ]
        return test_cases

    def standby_case_test(self) -> dict[str, bool]:
        """Tests the standby case."""
        test_cases: dict[str, bool] = {
            "min_velocity": False,
            "max_velocity": False,
            "min_altitude": False,
            "max_altitude": False,
            "apogee_prediction": False,
            "extensions": False,
        }
        # Check all conditions and update the test_cases dictionary
        test_cases["min_velocity"] = self.standby_case.min_velocity == pytest.approx(0.0, abs=0.1)
        test_cases["max_velocity"] = (
            self.standby_case.max_velocity <= TAKEOFF_VELOCITY_METERS_PER_SECOND
        )
        test_cases["min_altitude"] = (
            self.standby_case.min_altitude >= -6.0
        )  # might be negative due to noise/flakiness
        test_cases["max_altitude"] = self.standby_case.max_altitude <= GROUND_ALTITUDE_METERS
        test_cases["apogee_prediction"] = not any(self.standby_case.apogee_prediction)
        test_cases["extensions"] = (
            ServoExtension.MIN_EXTENSION in self.standby_case.extensions
            or ServoExtension.MIN_NO_BUZZ in self.standby_case.extensions
        )

        return test_cases

    def motor_burn_case_test(self) -> dict[str, bool]:
        """Test the motor burn case."""
        test_cases: dict[str, bool] = {
            "max_velocity": False,
            "max_avg_vertical_acceleration": False,
            "max_altitude": False,
            "apogee_prediction": False,
            "extensions": False,
        }

        # Check all conditions and update the test_cases dictionary
        test_cases["max_velocity"] = (
            self.motor_burn_case.max_velocity >= TAKEOFF_VELOCITY_METERS_PER_SECOND
            and self.motor_burn_case.max_velocity <= 300.0
        )  # haven't hit Mach 1
        test_cases["max_avg_vertical_acceleration"] = (
            self.motor_burn_case.max_avg_vertical_acceleration >= 90.0
        )
        test_cases["max_altitude"] = (
            self.motor_burn_case.max_altitude <= 500.0
        )  # motor burn time isn't that long
        test_cases["apogee_prediction"] = not any(self.motor_burn_case.apogee_prediction)
        test_cases["extensions"] = (
            ServoExtension.MIN_EXTENSION in self.motor_burn_case.extensions
            or ServoExtension.MIN_NO_BUZZ in self.motor_burn_case.extensions
        )

        return test_cases

    def coast_case_test(self) -> dict[str, bool]:
        """Tests the coast case."""
        test_cases: dict[str, bool] = {
            "max_velocity": False,
            "min_velocity": False,
            "max_altitude": False,
            "min_altitude": False,
            "extensions": False,
            "apogee_prediction": False,
        }
        # Check all conditions and update the test_cases dictionary
        # Velocity checks
        test_cases["max_velocity"] = (
            self.coast_case.max_velocity - 15 <= self.motor_burn_case.max_velocity
        )
        test_cases["min_velocity"] = (
            self.coast_case.min_velocity <= 11.0
        )  # velocity around apogee should be low

        # Altitude checks
        test_cases["min_altitude"] = (
            self.coast_case.min_altitude >= self.motor_burn_case.max_altitude
        )
        test_cases["max_altitude"] = self.coast_case.max_altitude <= self.target_apogee + 100

        # Apogee prediction check
        apogee_pred_list = self.coast_case.apogee_prediction
        median_predicted_apogee = statistics.median(apogee_pred_list)
        max_apogee = self.coast_case.max_altitude
        test_cases["apogee_prediction"] = (
            max_apogee * 0.9 <= median_predicted_apogee <= max_apogee * 1.1
        )

        # Extensions check
        test_cases["extensions"] = {
            ServoExtension.MIN_EXTENSION,
            ServoExtension.MIN_NO_BUZZ,
            ServoExtension.MAX_EXTENSION,
            ServoExtension.MAX_NO_BUZZ,
        }.issuperset(set(self.coast_case.extensions))

        return test_cases

    def free_fall_case_test(self) -> dict[str, bool]:
        """Tests the free fall case."""
        test_cases: dict[str, bool] = {
            "min_velocity": False,
            "max_velocity": False,
            "max_altitude": False,
            "min_altitude": False,
            "extensions": False,
        }
        # we have chute deployment, so we shouldn't go that fast
        test_cases["min_velocity"] = self.free_fall_case.min_velocity >= -30.0
        test_cases["max_velocity"] = self.free_fall_case.max_velocity <= 0.0
        # max altitude of both states should be about the same
        test_cases["max_altitude"] = self.coast_case.max_altitude == pytest.approx(
            self.free_fall_case.max_altitude, rel=5
        )
        # free fall should be close to ground:
        test_cases["min_altitude"] = (
            self.free_fall_case.min_altitude <= GROUND_ALTITUDE_METERS + 10.0
        )
        # Assert that only MIN_EXTENSION and MIN_NO_BUZZ are in the extensions list:
        test_cases["extensions"] = (
            ServoExtension.MIN_EXTENSION in self.free_fall_case.extensions
            or ServoExtension.MIN_NO_BUZZ in self.free_fall_case.extensions
        )
        return test_cases

    def landed_case_test(self) -> dict[str, bool]:
        """Tests the landed case."""
        test_cases: dict[str, bool] = {
            "max_avg_vertical_acceleration": False,
            "max_velocity": False,
            "min_altitude": False,
            "max_altitude": False,
            "extensions": False,
        }
        # Check all conditions and update the test_cases dictionary
        test_cases["max_avg_vertical_acceleration"] = (
            self.landed_case.max_avg_vertical_acceleration
            >= LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED
        )
        test_cases["max_velocity"] = self.landed_case.max_velocity <= 0.1
        test_cases["min_altitude"] = self.landed_case.min_altitude <= GROUND_ALTITUDE_METERS
        test_cases["max_altitude"] = self.landed_case.max_altitude <= GROUND_ALTITUDE_METERS + 10.0
        test_cases["extensions"] = (
            ServoExtension.MIN_EXTENSION in self.landed_case.extensions
            or ServoExtension.MIN_NO_BUZZ in self.landed_case.extensions
        )

        return test_cases

    def log_file_lines_test(self, lines_in_log_file: int) -> bool:
        """Tests the number of lines in the log file."""
        return lines_in_log_file > 80_000

    def log_file_states_logged(self, state_letter_list: list[str]) -> bool:
        """Tests if all states were logged."""
        return state_letter_list == ["S", "M", "C", "F", "L"]


class PurpleLaunchCase(LaunchCase):
    """The test case for the purple launch data."""

    def free_fall_case_test(self):
        test_cases = super().free_fall_case_test()
        # Update the min_velocity test case:
        test_cases["min_velocity"] = self.free_fall_case.min_velocity <= -300.0
        return test_cases


class InterestLaunchCase(LaunchCase):
    """The test case for the interest launch data."""


class GenesisLaunchCase(LaunchCase):
    """The test case for the genesis launch data."""


class LegacyLaunchCase(LaunchCase):
    """The test case for the legacy launch data."""

    def free_fall_case_test(self):
        test_cases = super().free_fall_case_test()
        # Update the min_velocity and max_velocity test case:
        test_cases["min_velocity"] = self.free_fall_case.min_velocity <= -100.0
        test_cases["max_velocity"] = self.free_fall_case.max_velocity <= 10.0
        return test_cases


class PelicanatorLaunchCase1(LaunchCase):
    """The test case for the pelicanator launch data 1."""

    def test_all_states_present(self):
        # Check we have all the states:
        test_cases = super().test_all_states_present()
        test_cases["length_states_dict"] = len(self.states_dict) == 4
        # Order of states matters!
        test_cases["order_states_dict"] = list(self.states_dict.keys()) == [
            "StandbyState",
            "MotorBurnState",
            "CoastState",
            "FreeFallState",
        ]
        return test_cases

    def free_fall_case_test(self):
        test_cases = super().free_fall_case_test()
        # The data was cutoff in free fall state, so the min altitude is not accurate:
        test_cases["min_altitude"] = True

        # Our min velocity was high since the chutes didn't deploy right:
        test_cases["min_velocity"] = self.free_fall_case.min_velocity >= -50.0
        return test_cases

    def landed_case_test(self):
        """No landed state, just return a dict with True values."""
        test_cases: dict[str, bool] = {
            "max_avg_vertical_acceleration": True,
            "max_velocity": True,
            "min_altitude": True,
            "max_altitude": True,
            "extensions": True,
        }
        return test_cases

    def log_file_lines_test(self, lines_in_log_file: int) -> bool:
        """
        Tests the number of lines in the log file.

        Data got cutoff ~22 seconds before landing.
        """
        return lines_in_log_file > 35_000

    def log_file_states_logged(self, state_letter_list: list[str]) -> bool:
        """
        Tests if all states were logged.

        Data got cutoff ~22 seconds before landing.
        """
        return state_letter_list == ["S", "M", "C", "F"]


class PelicanatorLaunchCase2(LaunchCase):
    """The test case for the pelicanator launch data 2."""

    def free_fall_case_test(self):
        test_cases = super().free_fall_case_test()
        # Update the min_velocity test case, which was slightly high, maybe due to wind?
        test_cases["min_velocity"] = self.free_fall_case.min_velocity >= -40.0
        return test_cases
