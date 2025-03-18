"""Module which has the header panel for the flight display."""

from time import monotonic_ns
from typing import ClassVar, Literal

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Label, ProgressBar, Static

from airbrakes.context import AirbrakesContext
from airbrakes.graphics.custom_widgets import TimeDisplay
from airbrakes.graphics.utils import set_only_class
from airbrakes.utils import convert_ns_to_s


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

    action_decrease_sim_speed = decrease_speed
    action_increase_sim_speed = increase_speed


class FlightProgressBar(Static):
    """Panel displaying the flight progress bar. The color changes depending on the
    current state of the rocket."""

    def compose(self) -> ComposeResult:
        self.progress_bar = ProgressBar(
            id="progress-bar-widget",
            show_eta=False,
            show_percentage=False,
        )
        yield self.progress_bar

    def initialize_widgets(self, flight_length_seconds: int) -> None:
        """Initializes the progress bar with the total flight length."""
        self.progress_bar.update(total=flight_length_seconds)

    def set_progress(self, current_flight_time_sec: float) -> None:
        """Updates the progress bar with the current flight time."""
        self.progress_bar.update(progress=current_flight_time_sec)

    def update_progress_bar_color(
        self, state: Literal["Standby", "MotorBurn", "Coast", "FreeFall", "Landed"]
    ) -> None:
        """Updates the progress bar color based on the current flight state."""
        inner_bar = self.progress_bar.query_one("#bar")
        set_only_class(inner_bar, state.lower())


class FlightHeader(Static):
    """Panel displaying the launch file name, launch time, and simulation status."""

    state: reactive[str] = reactive("Standby")

    context: AirbrakesContext | None = None
    t_zero_time_ns = reactive(0)
    takeoff_time_ns = 0
    sim_start_time: int = 0
    current_sim_time: reactive[int] = reactive(0)
    is_mock: bool = True
    _pre_calculated_motor_burn_time_ns: int | None = None

    def compose(self) -> ComposeResult:
        """Composes the header panel."""
        # Grid layout, 4 rows, 3 columns:
        yield Label("", id="launch-file-name", disabled=True)
        yield Label("00:00.00", id="normal-sim-time")
        yield Static()
        yield Static()
        yield TimeDisplay("T+00:00", id="launch-clock")
        yield Static()
        yield Label("STATUS: ", id="state")
        yield SimulationSpeed(id="sim-speed-panel")
        yield Static()
        # Takes all the columns in the last row:
        yield FlightProgressBar(id="flight-progress-bar")

    def initialize_widgets(self, context: AirbrakesContext, is_mock: bool) -> None:
        """Initializes the widgets with the context and the mock flag."""
        self.context = context
        self.is_mock = is_mock
        self.query_one(SimulationSpeed).sim_speed = self.context.imu._sim_speed_factor.value

        file_name = self.query_one("#launch-file-name", Label)

        if file_name.disabled:
            launch_file_name = self.context.imu._log_file_path.stem.replace("_", " ").title()
            file_name.update(launch_file_name)
            file_name.disabled = False

        if not self._pre_calculated_motor_burn_time_ns:
            self._pre_calculated_motor_burn_time_ns = self.context.imu.get_launch_time()

        # Get the flight length from the metadata, so we can update the progress bar:
        file_metadata = self.context.imu.file_metadata
        flight_length = file_metadata["flight_data"]["flight_length_seconds"]

        self.query_one(FlightProgressBar).initialize_widgets(flight_length)

        self.sim_start_time = monotonic_ns()

    def watch_t_zero_time_ns(self) -> None:
        """Updates the launch time display, and the progress bar."""
        # Update the launch time display:
        time_display = self.query_one("#launch-clock", TimeDisplay)
        after_launch = self.t_zero_time_ns > 0
        launch_time = TimeDisplay.format_ns_to_min_s_ms(abs(self.t_zero_time_ns))
        launch_time = f"T+{launch_time}" if after_launch else f"T-{launch_time}"
        time_display.update(launch_time)

        # Update the progress bar with the launch time:
        launch_time_seconds = convert_ns_to_s(self.t_zero_time_ns)
        self.query_one(FlightProgressBar).set_progress(launch_time_seconds)

    def watch_state(self) -> None:
        if not self.context:
            return
        state_label = self.query_one("#state", Label)

        if not self.takeoff_time_ns and self.state == "MotorBurnState":
            self.takeoff_time_ns = self.context.state.start_time_ns

        label = self.state.removesuffix("State")
        state_label.update(f"STATUS: {label}")
        self.query_one(FlightProgressBar).update_progress_bar_color(label)

    def watch_current_sim_time(self) -> None:
        time_display = self.query_one("#normal-sim-time", Label)
        time_display.update(TimeDisplay.format_ns_to_min_s_ms(self.current_sim_time))

    def calculate_launch_time(self) -> int:
        """
        Calculates the launch time relative to the start of motor burn.
        :return: The launch time in nanoseconds relative to the start of motor burn.
        """
        # Just update our launch time, if it was set (see watch_state)
        if self.takeoff_time_ns:
            current_timestamp = self.context.data_processor.current_timestamp
            return current_timestamp - self.takeoff_time_ns

        # We are before launch (T-0). Only happens when running a mock:
        if self.is_mock:
            current_timestamp = self.context.data_processor.current_timestamp
            return current_timestamp - self._pre_calculated_motor_burn_time_ns

        return 0

    def update_header(self) -> None:
        self.state = self.context.state.name
        self.t_zero_time_ns = self.calculate_launch_time()
        self.current_sim_time = monotonic_ns() - self.sim_start_time
