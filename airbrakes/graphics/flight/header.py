"""Module which has the header panel for the flight display."""

from time import monotonic_ns
from typing import ClassVar

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Label, Static

from airbrakes.airbrakes import AirbrakesContext
from airbrakes.graphics.custom_widgets import TimeDisplay


class SimulationSpeed(Static, can_focus=True):
    """Panel displaying the current simulation speed, with buttons to change it."""

    BINDINGS: ClassVar[list] = [
        ("comma", "decrease_sim_speed", "Dec. speed"),
        ("full_stop", "increase_sim_speed", "Inc. speed"),
        ("space", "pause_sim", "Pause sim"),
        ("space", "play_sim", "Play sim"),
    ]

    sim_speed: reactive[float] = reactive(1.0, bindings=True)
    old_sim_speed: float = 1.0

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Button("<", id="speed_decrease_button")
            yield Label("1.0x", id="simulation_speed")
            yield Button(">", id="speed_increase_button")

    def validate_sim_speed(self, sim_speed: float) -> float:
        if sim_speed < 0.0:
            return 0
        if sim_speed > 2.0:
            return 2.0
        return round(sim_speed, 2)

    def watch_sim_speed(self, old_sim_speed: float, sim_speed: float) -> None:
        self.query_one("#simulation_speed", Label).update(f"{sim_speed:.1f}x")
        self.old_sim_speed = old_sim_speed

    def action_pause_sim(self) -> None:
        self.sim_speed = 0.0

    def action_play_sim(self) -> None:
        self.sim_speed = self.old_sim_speed

    @on(Button.Pressed, "#speed_decrease_button")
    def decrease_speed(self) -> None:
        self.sim_speed -= 0.1

    @on(Button.Pressed, "#speed_increase_button")
    def increase_speed(self) -> None:
        self.sim_speed += 0.1

    def check_action(self, action: str, _: tuple[object, ...]) -> bool | None:
        if action == "decrease_sim_speed" and self.sim_speed <= 0.0:
            return None
        if action == "increase_sim_speed" and self.sim_speed >= 2.0:
            return None
        if action == "pause_sim":
            return self.sim_speed != 0.0
        if action == "play_sim":
            return self.sim_speed == 0.0
        return True

    def action_decrease_sim_speed(self) -> None:
        self.sim_speed -= 0.1

    def action_increase_sim_speed(self) -> None:
        self.sim_speed += 0.1


class FlightHeader(Static):
    """Panel displaying the launch file name, launch time, and simulation status."""

    state: reactive[str] = reactive("Standby")

    airbrakes: AirbrakesContext | None = None
    t_zero_time = reactive(0)
    takeoff_time = 0
    sim_start_time: int = 0
    current_sim_time: reactive[int] = reactive(0)
    is_mock: bool = True
    _pre_calculated_motor_burn_time: int | None = None

    def compose(self) -> ComposeResult:
        yield Label("", id="launch-file-name", disabled=True)
        yield Label("00:00.00", id="normal-sim-time")
        yield Static()
        yield Static()
        yield TimeDisplay("T+00:00", id="launch-clock")
        yield Static()
        yield Label("STATUS: ", id="state")
        yield SimulationSpeed(id="sim-speed-panel")

    def watch_t_zero_time(self) -> None:
        time_display = self.query_one("#launch-clock", TimeDisplay)
        after_launch = self.t_zero_time > 0
        launch_time = TimeDisplay.format_ns_to_min_s_ms(abs(self.t_zero_time))
        launch_time = f"T+{launch_time}" if after_launch else f"T-{launch_time}"
        time_display.update(launch_time)

    def watch_state(self) -> None:
        state_label = self.query_one("#state", Label)

        if not self.takeoff_time and self.state == "MotorBurnState":
            self.takeoff_time = self.airbrakes.state.start_time_ns

        label = self.state.removesuffix("State")
        state_label.update(f"STATUS: {label}")

    def watch_current_sim_time(self) -> None:
        time_display = self.query_one("#normal-sim-time", Label)
        time_display.update(TimeDisplay.format_ns_to_min_s_ms(self.current_sim_time))

    def initialize_widgets(self, airbrakes: AirbrakesContext, is_mock: bool) -> None:
        self.airbrakes = airbrakes
        self.is_mock = is_mock
        self.query_one(SimulationSpeed).sim_speed = self.airbrakes.imu._sim_speed_factor.value

        file_name = self.query_one("#launch-file-name", Label)

        if file_name.disabled:
            launch_file_name = self.airbrakes.imu._log_file_path.stem.replace("_", " ").title()
            file_name.update(launch_file_name)
            file_name.disabled = False

        if not self._pre_calculated_motor_burn_time:
            self._pre_calculated_motor_burn_time = self.airbrakes.imu.get_launch_time()

        self.sim_start_time = monotonic_ns()

    def calculate_launch_time(self) -> int:
        """
        Calculates the launch time relative to the start of motor burn.
        :return: The launch time in nanoseconds relative to the start of motor burn.
        """
        # Just update our launch time, if it was set (see watch_state)
        if self.takeoff_time:
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            return current_timestamp - self.takeoff_time

        # We are before launch (T-0). Only happens when running a mock:
        if self.is_mock:
            current_timestamp = self.airbrakes.data_processor.current_timestamp
            return current_timestamp - self._pre_calculated_motor_burn_time

        return 0

    def update_header(self) -> None:
        self.state = self.airbrakes.state.name
        self.t_zero_time = self.calculate_launch_time()
        self.current_sim_time = monotonic_ns() - self.sim_start_time
