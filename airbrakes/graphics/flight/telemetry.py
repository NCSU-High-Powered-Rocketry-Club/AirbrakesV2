"""Module which has the 2 telemetry panels for the flight display."""

from textual.app import ComposeResult
from textual.reactive import reactive, var
from textual.widgets import Label, Static

from airbrakes.airbrakes import AirbrakesContext


class DebugTelemetry(Static):
    """Collapsible panel for displaying debug telemetry data."""

    airbrakes: AirbrakesContext
    imu_queue_size = reactive(0)
    cpu_usage = reactive("")
    state = var("Standby")
    apogee = var(0.0)
    apogee_convergence_time = reactive(0.0)
    alt_at_convergence = reactive(0.0)
    apogee_at_convergence = reactive(0.0)
    log_buffer_size = reactive(0)
    fetched_packets = reactive(0)
    coast_start_time = 0

    def compose(self) -> ComposeResult:
        yield Label("IMU Queue Size: ", id="imu_queue_size", expand=True)
        yield Label("Convergence Time: ", id="apogee_convergence_time")
        yield Label("Convergence Height: ", id="alt_at_convergence")
        yield Label("Pred. Apogee at Convergence: ", id="apogee_at_convergence")
        yield Label("Fetched packets: ", id="fetched_packets", expand=True)
        yield Label("Log buffer size: ", id="log_buffer_size")
        yield Label("CPU Usage: ", id="cpu_usage")

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes

    def watch_imu_queue_size(self) -> None:
        imu_queue_size_label = self.query_one("#imu_queue_size", Label)
        imu_queue_size_label.update(f"IMU Queue Size: {self.imu_queue_size}")

    def watch_state(self) -> None:
        if self.state == "CoastState":
            self.coast_start_time = self.airbrakes.state.start_time_ns

    def watch_apogee(self) -> None:
        if self.coast_start_time and not self.apogee_convergence_time:
            self.apogee_convergence_time = (
                self.airbrakes.data_processor.current_timestamp - self.coast_start_time
            ) * 1e-9
            self.alt_at_convergence = self.airbrakes.data_processor.current_altitude
            self.apogee_at_convergence = self.apogee

    def watch_apogee_convergence_time(self) -> None:
        apogee_convergence_time_label = self.query_one("#apogee_convergence_time", Label)
        apogee_convergence_time_label.update(
            f"Convergence Time: {self.apogee_convergence_time:.2f} s"
        )

    def watch_alt_at_convergence(self) -> None:
        alt_at_convergence_label = self.query_one("#alt_at_convergence", Label)
        alt_at_convergence_label.update(f"Convergence Height: {self.alt_at_convergence:.2f} m")

    def watch_apogee_at_convergence(self) -> None:
        apogee_at_convergence_label = self.query_one("#apogee_at_convergence", Label)
        apogee_at_convergence_label.update(
            f"Pred. Apogee at Convergence: {self.apogee_at_convergence:.2f} m"
        )

    def watch_log_buffer_size(self) -> None:
        log_buffer_size_label = self.query_one("#log_buffer_size", Label)
        log_buffer_size_label.update(f"Log buffer size: {self.log_buffer_size} packets")

    def watch_fetched_packets(self) -> None:
        fetched_packets_label = self.query_one("#fetched_packets", Label)
        fetched_packets_label.update(f"Fetched packets: {self.fetched_packets}")

    def watch_cpu_usage(self) -> None:
        cpu_usage_label = self.query_one("#cpu_usage", Label)
        cpu_usage_label.update(f"CPU Usage: {self.cpu_usage}")

    def update_debug_telemetry(self) -> None:
        self.imu_queue_size = self.airbrakes.imu._data_queue.qsize()
        self.log_buffer_size = len(self.airbrakes.logger._log_buffer)
        self.apogee = self.airbrakes.apogee_predictor.apogee
        self.fetched_packets = len(self.airbrakes.imu_data_packets)
        self.state = self.airbrakes.state.name
        # self.cpu_usage = cpu_usage


class FlightTelemetry(Static):
    """Panel displaying real-time flight information."""

    airbrakes: AirbrakesContext
    vertical_velocity = reactive(0.0)
    max_vertical_velocity = reactive(0.0)
    current_height = reactive(0.0)
    max_height = reactive(0.0)
    apogee_prediction = reactive(0.0)
    airbrakes_extension = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Label("Velocity: ", id="vertical_velocity", expand=True)
        yield Label("Max Velocity: ", id="max_vertical_velocity")
        yield Label("Altitude: ", id="current_height")
        yield Label("Max altitude: ", id="max_height", expand=True)
        yield Label("Predicted Apogee: ", id="apogee_prediction")
        yield Label("Airbrakes Extension: ", id="airbrakes_extension")

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes

    def watch_vertical_velocity(self) -> None:
        vertical_velocity_label = self.query_one("#vertical_velocity", Label)
        vertical_velocity_label.update(f"Velocity: {self.vertical_velocity:.2f} m/s")

    def watch_max_vertical_velocity(self) -> None:
        max_vertical_velocity_label = self.query_one("#max_vertical_velocity", Label)
        max_vertical_velocity_label.update(f"Max Velocity: {self.max_vertical_velocity:.2f} m/s")

    def watch_current_height(self) -> None:
        current_height_label = self.query_one("#current_height", Label)
        current_height_label.update(f"Altitude: {self.current_height:.2f} m")

    def watch_max_height(self) -> None:
        max_height_label = self.query_one("#max_height", Label)
        max_height_label.update(f"Max altitude: {self.max_height:.2f} m")

    def watch_apogee_prediction(self) -> None:
        apogee_prediction_label = self.query_one("#apogee_prediction", Label)
        apogee_prediction_label.update(f"Predicted Apogee: {self.apogee_prediction:.2f} m")

    def watch_airbrakes_extension(self) -> None:
        airbrakes_extension_label = self.query_one("#airbrakes_extension", Label)
        airbrakes_extension_label.update(f"Airbrakes Extension: {self.airbrakes_extension:.2f}")

    def update_flight_telemetry(self) -> None:
        self.vertical_velocity = self.airbrakes.data_processor.vertical_velocity
        self.max_vertical_velocity = self.airbrakes.data_processor.max_vertical_velocity
        self.current_height = self.airbrakes.data_processor.current_altitude
        self.max_height = self.airbrakes.data_processor.max_altitude
        self.apogee_prediction = self.airbrakes.apogee_predictor.apogee
        self.airbrakes_extension = self.airbrakes.current_extension.value
