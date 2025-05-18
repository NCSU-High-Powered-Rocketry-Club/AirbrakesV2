"""
Module which has the 2 telemetry panels for the flight display.
"""

from textual.app import ComposeResult
from textual.containers import Grid
from textual.reactive import reactive, var
from textual.widgets import Label, Static

from airbrakes.context import Context
from airbrakes.graphics.bases.base_telemetry import (
    BaseDebugTelemetry,
    BaseFlightTelemetry,
    BaseQueueSizesTelemetry,
)


class ReplayFlightTelemetry(BaseFlightTelemetry):
    """
    Panel displaying real-time flight information.
    """

    total_velocity = reactive(0.0)
    max_total_velocity = reactive(0.0)
    pressure_alt = reactive(0.0)
    max_pressure_alt = reactive(0.0)
    apogee_prediction = reactive(0.0)

    __slots__ = (
        "apogee_label",
        "debug_telemetry",
        "max_pressure_alt_label",
        "max_total_velocity_label",
        "pressure_alt_label",
        "total_velocity_label",
    )

    def compose(self) -> ComposeResult:
        with Grid(id="flight-telemetry-grid"):  # Declared with 5 colums in tcss file
            # Row 1:
            yield from self._compose_vertical_acceleration_label()

            # Row 2:
            yield from self._compose_vertical_velocity_label()

            # Row 3:
            yield Static("Total Velocity:", id="total-velocity-static-label")
            self.total_velocity_label = Label("0.0", id="total-velocity-label", expand=True)
            yield self.total_velocity_label
            yield Static("Max:", id="max-total-velocity-static-label")
            self.max_total_velocity_label = Label("0.0", id="max-total-velocity-label", expand=True)
            yield self.max_total_velocity_label
            yield Static("m/s", id="total-velocity-units-static-label", classes="units")

            # Row 4:
            yield from self._compose_current_altitude_label()

            # Row 5:
            yield Static("Pressure Alt:", id="pressure-altitude-static-label")
            self.pressure_alt_label = Label("0.0", id="pressure-altitude-label", expand=True)
            yield self.pressure_alt_label
            yield Static("Max:", id="max-pressure-altitude-static-label")
            self.max_pressure_alt_label = Label(
                "0.0", id="max-pressure-altitude-label", expand=True
            )
            yield self.max_pressure_alt_label
            yield Static("m", id="pressure-altitude-units-static-label", classes="units")

            # Row 6:
            yield Static("Predicted Apogee:", id="predicted-apogee-static-label")
            self.apogee_label = Label("0.0", id="predicted-apogee-label", expand=True)
            yield self.apogee_label
            yield Static()
            yield Static()
            yield Static("m", id="apogee-units-static-label", classes="units")

            # Row 7:
            yield from self._compose_airbrakes_extension_label()

        self.debug_telemetry = ReplayDebugTelemetry(id="debug-telemetry")
        self.debug_telemetry.border_title = "DEBUG TELEMETRY"
        yield self.debug_telemetry

    def initialize_widgets(self, context: Context) -> None:
        super().initialize_widgets(context)
        self.context = context
        self.debug_telemetry.initialize_widgets(context)

    def reset_widgets(self) -> None:
        """
        Resets the widgets to their initial state.
        """
        self.debug_telemetry.reset_widgets()

    def watch_total_velocity(self) -> None:
        self.total_velocity_label.update(f"{self.total_velocity:.2f}")

    def watch_max_total_velocity(self) -> None:
        self.max_total_velocity_label.update(f"{self.max_total_velocity:.2f}")

    def watch_pressure_alt(self) -> None:
        self.pressure_alt_label.update(f"{self.pressure_alt:.2f}")

    def watch_max_pressure_alt(self) -> None:
        self.max_pressure_alt_label.update(f"{self.max_pressure_alt:.2f}")

    def watch_apogee_prediction(self) -> None:
        self.apogee_label.update(f"{self.apogee_prediction:.2f}")

    def update_telemetry(self) -> None:
        super().update_telemetry()
        self.max_vertical_acceleration = self.context.data_processor.max_vertical_acceleration
        self.total_velocity = self.context.data_processor.total_velocity
        self.max_total_velocity = self.context.data_processor.max_total_velocity
        self.apogee_prediction = self.context.last_apogee_predictor_packet.predicted_apogee
        self.pressure_alt = self.context.data_processor.current_pressure_altitude
        self.max_pressure_alt = self.context.data_processor.max_pressure_altitude

        self.debug_telemetry.update_telemetry()


class ReplayQueueSizesTelemetry(BaseQueueSizesTelemetry):
    """
    Modifies the QueueSizesTelemetry to not use the real hardware queue size.
    """

    __slots__ = ()

    def watch_imu_packets_per_cycle(self) -> None:
        """
        This function will be a no-op, since we don't have a real IMU.
        """

    def initialize_widgets(self, context: Context) -> None:
        """
        Overrides the initialize_widgets function to change the label of real hardware to "N/A".
        """
        super().initialize_widgets(context)
        self.imu_packets_per_cycle_label.update("N/A")


class ReplayDebugTelemetry(BaseDebugTelemetry):
    """
    Collapsible panel for displaying debug telemetry data, only the for mock replay.
    """

    state = var("Standby", init=False)
    apogee = reactive(0.0, init=False)

    __slots__ = (
        "alt_convergence_label",
        "apogee_convergence_time",
        "coast_start_time",
        "convergence_time_label",
        "first_apogee_label",
        "replay_queue_size_telemetry",
    )

    def compose(self) -> ComposeResult:
        with Grid(id="debug-telemetry-grid"):  # Declared with 3 columns in tcss file
            # Row 1:
            yield from self._compose_average_pitch_label()

            # Row 2:
            yield Static("First Apogee:", id="apogee-static-label")
            self.first_apogee_label = Label("0.0", id="first-apogee-label")
            yield self.first_apogee_label
            yield Static("m", id="apogee-units", classes="units")

            # Row 3:
            yield Static("Convergence Time:", id="apogee-convergence-time-static-label")
            self.convergence_time_label = Label("0.0", id="apogee-convergence-time-label")
            yield self.convergence_time_label
            yield Static("s", id="convergence-time-units", classes="units")

            # Row 4:
            yield Static("Convergence Height:", id="alt-at-convergence-static-label")
            self.alt_convergence_label = Label("0.0", id="altitude-at-convergence-label")
            yield self.alt_convergence_label
            yield Static("m", id="altitude-at-convergence-units", classes="units")

            # Row 5:
            yield from self._compose_invalid_fields_label()

        self.replay_queue_size_telemetry = ReplayQueueSizesTelemetry(id="queue-sizes-telemetry")
        yield self.replay_queue_size_telemetry

        yield from self._compose_cpu_usage_widget()

    def initialize_widgets(self, context: Context) -> None:
        super().initialize_widgets(context)
        self.coast_start_time = 0
        self.apogee_convergence_time = 0.0
        self.replay_queue_size_telemetry.initialize_widgets(context)

    def reset_widgets(self) -> None:
        """
        Resets the widgets to their initial state.
        """
        # Reinitialize class variables in case we are restarting a flight:
        self.apogee_convergence_time = 0.0
        self.convergence_time_label.update("0.0")
        self.alt_convergence_label.update("0.0")
        self.first_apogee_label.update("0.0")
        self.coast_start_time = 0

    def watch_state(self) -> None:
        if self.state == "CoastState":
            self.coast_start_time = self.context.state.start_time_ns

    def watch_apogee(self) -> None:
        if self.coast_start_time and not self.apogee_convergence_time:
            self.apogee_convergence_time = (
                self.context.data_processor.current_timestamp - self.coast_start_time
            ) * 1e-9
            self.convergence_time_label.update(f"{self.apogee_convergence_time:.2f}")
            self.alt_convergence_label.update(f"{self.context.data_processor.current_altitude:.2f}")
            self.first_apogee_label.update(f"{self.apogee:.2f}")

    def update_telemetry(self) -> None:
        super().update_telemetry()
        self.apogee = self.context.last_apogee_predictor_packet.predicted_apogee
        self.state = self.context.state.name
        self.replay_queue_size_telemetry.update_queue_sizes_telemetry()
