"""
This module contains the test cases for the launch data.

The test cases are used in test_integration.py to test the launch data.
"""

import inspect
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
    """
    Records the values achieved by the airbrakes system in a particular state.
    """

    min_velocity: float | None = None
    max_velocity: float | None = None
    extensions: list[ServoExtension] = []
    min_altitude: float | None = None
    max_altitude: float | None = None
    min_avg_vertical_acceleration: float | None = None
    max_avg_vertical_acceleration: float | None = None
    apogee_prediction: list[float] = []


class CaseResult(msgspec.Struct):
    """
    Records the result of a test case.
    """

    case_name: str
    error_cases: dict[str, ValueError] = msgspec.field(default_factory=dict)
    """
    The error details of the test case.

    If the test case passed, this will be an empty dict. The keys are the names of the particular
    test case that failed the test, and the values are the error messages. For example, if the
    min_velocity was not as expected, the error_cases will be: {     "min_velocity":
    ValueError("min_velocity failed: Got 5.0") }
    """

    @property
    def passed(self) -> bool:
        """
        If all the test subcases passed.

        Returns:
            bool: True if all test cases passed.

        Raises:
            ExceptionGroup: If there are any error cases, it will raise an ExceptionGroup with the
            error cases.
        """
        if self.error_cases:
            raise ExceptionGroup(
                f"{len(self.error_cases)} Test cases failed for {self.case_name}:",
                list(self.error_cases.values()),
            )
        return True

    def consider_case(self, name: str, attribute_value: str, result: bool) -> None:
        """
        Adds a case to the error_cases dictionary if the result is False.

        If there is already an error case, it will overwrite it with the new one. Also modifies the
        traceback to point to the line where the case was considered.
        """
        if not result:
            current_frame = inspect.currentframe()
            caller_frame = current_frame.f_back
            # Create artificial traceback chain
            tb = None
            # Build traceback to include the caller
            if caller_frame and current_frame:
                tb = types.TracebackType(
                    tb_next=None,
                    tb_frame=caller_frame,
                    tb_lasti=caller_frame.f_lasti,
                    tb_lineno=caller_frame.f_lineno,
                )
            error = ValueError(f"{name} failed: Got {attribute_value}")
            error.__traceback__ = tb
            error.add_note(f"Hint: You might want to edit the {self.case_name} test case.")
            self.error_cases[name] = error
        else:
            self.error_cases.pop(name, None)


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

    def all_states_present(self) -> CaseResult:
        """
        Tests whether all states are present in the states_dict.
        """
        # Check we have all the states:
        case_result = CaseResult("states presence")
        case_result.consider_case(
            "length_states_dict",
            str(len(self.states_dict)),
            len(self.states_dict) == 5,
        )

        case_result.consider_case(
            "order_states_dict",
            str(list(self.states_dict.keys())),
            # Order of states matters!
            list(self.states_dict.keys())
            == [
                "StandbyState",
                "MotorBurnState",
                "CoastState",
                "FreeFallState",
                "LandedState",
            ],
        )
        return case_result

    def standby_case_test(self) -> CaseResult:
        """
        Tests the standby case.
        """
        case_result = CaseResult("standby case")
        # Check all conditions and update the test_cases dictionary
        case_result.consider_case(
            "min_velocity",
            str(self.standby_case.min_velocity),
            self.standby_case.min_velocity == pytest.approx(0.0, abs=0.1),
        )
        case_result.consider_case(
            "max_velocity",
            str(self.standby_case.max_velocity),
            self.standby_case.max_velocity <= TAKEOFF_VELOCITY_METERS_PER_SECOND,
        )

        case_result.consider_case(
            "min_altitude",
            str(self.standby_case.min_altitude),
            self.standby_case.min_altitude >= -6.0,  # might be negative due to noise/flakiness
        )

        case_result.consider_case(
            "max_altitude",
            str(self.standby_case.max_altitude),
            self.standby_case.max_altitude <= GROUND_ALTITUDE_METERS,
        )
        case_result.consider_case(
            "apogee_prediction",
            str(self.standby_case.apogee_prediction),
            not any(self.standby_case.apogee_prediction),
        )
        case_result.consider_case(
            "extensions",
            str(self.standby_case.extensions),
            (
                ServoExtension.MIN_EXTENSION in self.standby_case.extensions
                or ServoExtension.MIN_NO_BUZZ in self.standby_case.extensions
            ),
        )

        return case_result

    def motor_burn_case_test(self) -> CaseResult:
        """
        Test the motor burn case.
        """
        case_result = CaseResult("motor burn case")

        case_result.consider_case(
            "max_velocity",
            str(self.motor_burn_case.max_velocity),
            self.motor_burn_case.max_velocity >= TAKEOFF_VELOCITY_METERS_PER_SECOND
            and self.motor_burn_case.max_velocity <= 300.0,
            # haven't hit Mach 1
        )

        case_result.consider_case(
            "max_avg_vertical_acceleration",
            str(self.motor_burn_case.max_avg_vertical_acceleration),
            self.motor_burn_case.max_avg_vertical_acceleration >= 90.0,
        )

        case_result.consider_case(
            "max_altitude",
            str(self.motor_burn_case.max_altitude),
            self.motor_burn_case.max_altitude <= 500.0,
            # motor burn time isn't that long
        )

        case_result.consider_case(
            "apogee_prediction",
            str(self.motor_burn_case.apogee_prediction),
            not any(self.motor_burn_case.apogee_prediction),
        )

        case_result.consider_case(
            "extensions",
            str(self.motor_burn_case.extensions),
            (
                ServoExtension.MIN_EXTENSION in self.motor_burn_case.extensions
                or ServoExtension.MIN_NO_BUZZ in self.motor_burn_case.extensions
            ),
        )

        return case_result

    def coast_case_test(self) -> CaseResult:
        """
        Tests the coast case.
        """
        case_result = CaseResult("coast case")

        # Velocity checks
        case_result.consider_case(
            "max_velocity",
            str(self.coast_case.max_velocity),
            self.coast_case.max_velocity - 15 <= self.motor_burn_case.max_velocity,
        )

        case_result.consider_case(
            "min_velocity",
            str(self.coast_case.min_velocity),
            self.coast_case.min_velocity <= 11.0,
            # velocity around apogee should be low
        )

        # Altitude checks
        case_result.consider_case(
            "min_altitude",
            str(self.coast_case.min_altitude),
            self.coast_case.min_altitude >= self.motor_burn_case.max_altitude,
        )

        case_result.consider_case(
            "max_altitude",
            str(self.coast_case.max_altitude),
            self.coast_case.max_altitude <= self.target_apogee + 100.0,
        )

        # Apogee prediction check
        apogee_pred_list = self.coast_case.apogee_prediction
        median_predicted_apogee = statistics.median(apogee_pred_list)
        max_apogee = self.coast_case.max_altitude

        case_result.consider_case(
            "apogee_prediction",
            f"{max_apogee=} and {median_predicted_apogee=}, which is not a good prediction",
            max_apogee * 0.9 <= median_predicted_apogee <= max_apogee * 1.1,
        )

        # Extensions check
        case_result.consider_case(
            "extensions",
            f"{self.coast_case.extensions=} which should be a superset of the ServoExtensions",
            {
                ServoExtension.MIN_EXTENSION,
                ServoExtension.MIN_NO_BUZZ,
                ServoExtension.MAX_EXTENSION,
                ServoExtension.MAX_NO_BUZZ,
            }.issuperset(set(self.coast_case.extensions)),
        )

        return case_result

    def free_fall_case_test(self) -> CaseResult:
        """
        Tests the free fall case.
        """
        case_result = CaseResult("free fall case")

        # we have chute deployment, so we shouldn't go that fast
        case_result.consider_case(
            "min_velocity",
            str(self.free_fall_case.min_velocity),
            self.free_fall_case.min_velocity >= -40.0,
        )
        case_result.consider_case(
            "max_velocity",
            str(self.free_fall_case.max_velocity),
            self.free_fall_case.max_velocity <= 0.0,
        )

        # max altitude of both states should be about the same
        case_result.consider_case(
            "max_altitude",
            str(self.coast_case.max_altitude),
            self.coast_case.max_altitude == pytest.approx(self.free_fall_case.max_altitude, rel=5),
        )
        # free fall should be close to ground:
        case_result.consider_case(
            "min_altitude",
            str(self.free_fall_case.min_altitude),
            self.free_fall_case.min_altitude <= GROUND_ALTITUDE_METERS + 10.0,
        )
        # Assert that only MIN_EXTENSION and MIN_NO_BUZZ are in the extensions list:
        case_result.consider_case(
            "extensions",
            str(self.free_fall_case.extensions),
            (
                ServoExtension.MIN_EXTENSION in self.free_fall_case.extensions
                or ServoExtension.MIN_NO_BUZZ in self.free_fall_case.extensions
            ),
        )
        return case_result

    def landed_case_test(self) -> CaseResult:
        """
        Tests the landed case.
        """
        case_result = CaseResult("landed case")
        case_result.consider_case(
            "max_avg_vertical_acceleration",
            str(self.landed_case.max_avg_vertical_acceleration),
            self.landed_case.max_avg_vertical_acceleration
            >= LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED,
        )
        case_result.consider_case(
            "max_velocity", str(self.landed_case.max_velocity), self.landed_case.max_velocity <= 0.1
        )
        case_result.consider_case(
            "min_altitude",
            str(self.landed_case.min_altitude),
            self.landed_case.min_altitude <= GROUND_ALTITUDE_METERS,
        )
        case_result.consider_case(
            "max_altitude",
            str(self.landed_case.max_altitude),
            self.landed_case.max_altitude <= GROUND_ALTITUDE_METERS + 10.0,
        )
        case_result.consider_case(
            "extensions",
            str(self.landed_case.extensions),
            ServoExtension.MIN_EXTENSION in self.landed_case.extensions
            or ServoExtension.MIN_NO_BUZZ in self.landed_case.extensions,
        )

        return case_result

    def log_file_lines_test(self, lines_in_log_file: int) -> bool:
        """
        Tests the number of lines in the log file.
        """
        return lines_in_log_file > 80_000

    def log_file_states_logged(self, state_letter_list: list[str]) -> bool:
        """
        Tests if all states were logged.
        """
        return state_letter_list == ["S", "M", "C", "F", "L"]


class PurpleLaunchCase(LaunchCase):
    """
    The test case for the purple launch data.
    """

    def free_fall_case_test(self) -> CaseResult:
        case_result = super().free_fall_case_test()
        # Update the min_velocity test case:
        case_result.consider_case(
            "min_velocity",
            str(self.free_fall_case.min_velocity),
            self.free_fall_case.min_velocity <= -300.0,
        )
        return case_result


class ShakeNBakeLaunchCase(LaunchCase):
    """
    The test case for the shake n bake launch data.
    """


class GenesisLaunchCase(LaunchCase):
    """
    The test case for the genesis launch data.
    """


class LegacyLaunchCase(LaunchCase):
    """
    The test case for the legacy launch data.
    """

    def free_fall_case_test(self) -> CaseResult:
        case_result = super().free_fall_case_test()
        # Update the min_velocity and max_velocity test case:
        case_result.consider_case(
            "min_velocity",
            str(self.free_fall_case.min_velocity),
            self.free_fall_case.min_velocity <= -100.0,
        )
        case_result.consider_case(
            "max_velocity",
            str(self.free_fall_case.max_velocity),
            self.free_fall_case.max_velocity <= 10.0,
        )
        return case_result


class PelicanatorLaunchCase1(LaunchCase):
    """
    The test case for the pelicanator launch data 1.
    """

    def all_states_present(self) -> CaseResult:
        # Check we have all the states:
        case_result = super().all_states_present()
        case_result.consider_case(
            "length_states_dict", str(len(self.states_dict)), len(self.states_dict) == 4
        )
        # Order of states matters!
        case_result.consider_case(
            "order_states_dict",
            str(list(self.states_dict.keys())),
            list(self.states_dict.keys())
            == [
                "StandbyState",
                "MotorBurnState",
                "CoastState",
                "FreeFallState",
            ],
        )
        return case_result

    def free_fall_case_test(self) -> CaseResult:
        case_result = super().free_fall_case_test()
        # The data was cutoff in free fall state, so the min altitude is not accurate:
        case_result.consider_case("min_altitude", str(self.free_fall_case.min_altitude), True)

        # Our min velocity was high since the chutes didn't deploy right:
        case_result.consider_case(
            "min_velocity",
            str(self.free_fall_case.min_velocity),
            self.free_fall_case.min_velocity >= -50.0,
        )
        return case_result

    def landed_case_test(self) -> CaseResult:
        """
        No landed state, just return a CaseResult.
        """
        return CaseResult("landed case")

    def log_file_lines_test(self, lines_in_log_file: int) -> bool:
        """
        Tests the number of lines in the log file.

        Data got cutoff ~22 seconds before landing.
        """
        return lines_in_log_file > 33_000

    def log_file_states_logged(self, state_letter_list: list[str]) -> bool:
        """
        Tests if all states were logged.

        Data got cutoff ~22 seconds before landing.
        """
        return state_letter_list == ["S", "M", "C", "F"]


class PelicanatorLaunchCase2(LaunchCase):
    """
    The test case for the pelicanator launch data 2.
    """


class PelicanatorLaunchCase4(LaunchCase):
    """
    The test case for the pelicanator launch data 4 (Huntsville 2024-25).
    """


class GovernmentWorkLaunchCase1(LaunchCase):
    """
    The test case for the "governmen't work" launch data (Subscale 2025).
    """

    def coast_case_test(self) -> CaseResult:
        case_result = super().coast_case_test()

        # Airbrakes were programmed to deploy instantly, target apogee was 0m.
        case_result.consider_case(
            "max_altitude",
            str(self.coast_case.max_altitude),
            self.coast_case.max_altitude <= 600.0,
        )
        return case_result

    def log_file_lines_test(self, lines_in_log_file: int) -> bool:
        """
        Tests the number of lines in the log file.

        Data was perfect, this was a short flight.
        """
        return lines_in_log_file > 71_000


class GovernmentWorkLaunchCase2(LaunchCase):
    """
    The test case for the "government work 2" launch data (Subscale Launch 2).
    """
