"""Module which has the 2 telemetry panels for the flight display."""

import multiprocessing

import psutil
from textual.app import ComposeResult
from textual.reactive import reactive, var
from textual.widgets import Label, Static
from textual.worker import Worker, get_current_worker

from airbrakes.context import Context
from airbrakes.graphics.utils import set_only_class


class DebugTelemetry(Static):
    """Collapsible panel for displaying debug telemetry data."""

    context: Context
    queued_imu_packets = reactive(0)
    cpu_usage = reactive("")
    state = var("Standby")
    apogee = var(0.0)
    apogee_convergence_time = reactive(0.0)
    average_pitch = reactive(0.0)
    average_acceleration = reactive(0.0)
    alt_at_convergence = reactive(0.0)
    apogee_at_convergence = reactive(0.0)
    log_buffer_size = reactive(0)
    retrieved_packets = reactive(0)
    coast_start_time = 0

    def compose(self) -> ComposeResult:
        yield Label("Average Pitch: ", id="average_pitch", expand=True)
        yield Label("Average Accel: ", id="average_acceleration", expand=True)
        yield Label("Queued packets: ", id="queued_imu_packets", expand=True)
        yield Label("Convergence Time: ", id="apogee_convergence_time")
        yield Label("Convergence Height: ", id="alt_at_convergence")
        yield Label("Pred. Ap. @ Conv: ", id="apogee_at_convergence")
        yield Label("Retrieved packets: ", id="retrieved_packets", expand=True)
        yield Label("Log buffer size: ", id="log_buffer_size")
        cpu_usage = CPUUsage(id="cpu_usage_widget")
        cpu_usage.border_title = "CPU Usage"
        yield cpu_usage

    def initialize_widgets(self, context: Context) -> None:
        self.context = context
        self.query_one(CPUUsage).initialize_widgets(context)

    def watch_queued_imu_packets(self) -> None:
        imu_queue_size_label = self.query_one("#queued_imu_packets", Label)
        imu_queue_size_label.update(f"Queued packets: {self.queued_imu_packets}")

    def watch_state(self) -> None:
        if self.state == "CoastState":
            self.coast_start_time = self.context.state.start_time_ns

    def watch_apogee(self) -> None:
        if self.coast_start_time and not self.apogee_convergence_time:
            self.apogee_convergence_time = (
                self.context.data_processor.current_timestamp - self.coast_start_time
            ) * 1e-9
            self.alt_at_convergence = self.context.data_processor.current_altitude
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
        apogee_at_convergence_label.update(f"Pred. Ap. @ Conv: {self.apogee_at_convergence:.2f} m")

    def watch_log_buffer_size(self) -> None:
        log_buffer_size_label = self.query_one("#log_buffer_size", Label)
        log_buffer_size_label.update(f"Log buffer size: {self.log_buffer_size} packets")

    def watch_retrieved_packets(self) -> None:
        fetched_packets_label = self.query_one("#retrieved_packets", Label)
        fetched_packets_label.update(f"Retrieved packets: {self.retrieved_packets}")

    def watch_average_pitch(self) -> None:
        average_pitch_label = self.query_one("#average_pitch", Label)
        average_pitch_label.update(f"Average Pitch: {self.average_pitch:.2f}\u00b0")

    def watch_average_acceleration(self) -> None:
        average_accel_label = self.query_one("#average_acceleration", Label)
        average_accel_label.update(f"Average Accel: {self.average_acceleration:.2f} m/s\u00b2")

    def update_debug_telemetry(self) -> None:
        self.average_pitch = self.context.data_processor.average_pitch
        self.average_acceleration = self.context.data_processor.average_vertical_acceleration
        self.queued_imu_packets = self.context.context_data_packet.queued_imu_packets
        self.retrieved_packets = self.context.context_data_packet.retrieved_imu_packets
        self.log_buffer_size = len(self.context.logger._log_buffer)
        self.apogee = self.context.last_apogee_predictor_packet.predicted_apogee
        self.state = self.context.state.name


class CPUBar(Static):
    """Represents a single CPU bar."""


class CPUBars(Static):
    """Represents a group of CPU bars."""

    LIGHT_SHADE = "\u2591" * 5
    MEDIUM_SHADE = "\u2592" * 5
    DARK_SHADE = "\u2593" * 5
    FULL_BLOCK = "\u2588" * 5

    def compose(self) -> ComposeResult:
        """Show 10 CPUBars."""
        for _ in range(10):
            bar = CPUBar(CPUBars.LIGHT_SHADE)
            bar.set_class(True, "inactive")
            yield bar

    def update_bars(self, usage: float) -> None:
        """Update the CPUBars with the new usage."""
        # There are 10 bars, so a usage of 10.0 would mean that the first bar
        # is full, and should be changed to FULL_BLOCK.
        # 0 <= usage <= 3.33 -> Use LIGHT_SHADE
        # usage <= 6.66 -> Use MEDIUM_SHADE
        # usage <= 10.0 -> Use DARK_SHADE
        # The other bars will be nothing (empty).
        # E.g. a usage of 14.5 would mean that the first bar is FULL_BLOCK,
        # the second bar is MEDIUM_SHADE, and the rest are empty.
        # Then we do the same for the next bar, and so on.
        bars: list[CPUBar] = reversed(list(self.children))
        solid_bars, shaded_block = usage // 10, usage % 10
        bars_to_update = int(solid_bars) + 1 if shaded_block > 0 else int(solid_bars)

        for i, bar in enumerate(bars):
            if i + 1 < bars_to_update and solid_bars:
                bar.update(CPUBars.FULL_BLOCK)
                set_only_class(bar, "active")
            elif i + 1 == bars_to_update and shaded_block > 0:
                if shaded_block <= 3.3:
                    bar.update(CPUBars.LIGHT_SHADE)
                elif shaded_block <= 6.66:
                    bar.update(CPUBars.MEDIUM_SHADE)
                elif shaded_block <= 10.0:
                    bar.update(CPUBars.DARK_SHADE)
                set_only_class(bar, "active")
            else:
                bar.update(CPUBars.LIGHT_SHADE)
                bar.remove_class("active")

        active_bars = [bar for bar in self.children if "active" in bar.classes]
        if usage < 25:
            cpu_color_class = "low"
        elif usage < 50:
            cpu_color_class = "medium"
        else:
            cpu_color_class = "high"

        for bar in active_bars:
            bar.add_class(cpu_color_class)


class CPUUsage(Static):
    """Panel displaying the CPU usage."""

    context: Context = None
    cpu_usages = reactive({})

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.processes: dict[str, psutil.Process] = {}
        self.set_reactive(CPUUsage.cpu_usages, {})
        self.cpu_worker: Worker = None

    def compose(self) -> ComposeResult:
        # 3x4 grid:
        # TODO: Dynamically adjust the number of columns based on the number of processes.
        yield CPUBars(id="cpu_main_bar")
        yield CPUBars(id="cpu_imu_bar")
        yield CPUBars(id="cpu_log_bar")
        yield CPUBars(id="cpu_apogee_bar")
        # yield CPUBars(id="cpu_cam_bar")
        yield Label("00.0%", id="cpu_main_pct", expand=True)
        yield Label("00.0%", id="cpu_imu_pct", expand=True)
        yield Label("00.0%", id="cpu_log_pct", expand=True)
        yield Label("00.0%", id="cpu_apogee_pct", expand=True)
        # yield Label("00.0%", id="cpu_cam_pct", expand=True)
        yield Label("Main", id="cpu_main_label", expand=True)
        yield Label("IMU", id="cpu_imu_label", expand=True)
        yield Label("Log", id="cpu_log_label", expand=True)
        yield Label("Apogee", id="cpu_apogee_label", expand=True)
        # yield Label("Cam", id="cpu_cam_label", expand=True)

    def initialize_widgets(self, context: Context) -> None:
        self.context = context

    def start(self) -> None:
        self.processes = self.prepare_process_dict()
        self.worker = self.run_worker(
            self.update_cpu_usage, name="CPU Polling", thread=True, exclusive=True
        )

    def stop(self) -> None:
        self.worker.cancel()

    def update_labels(self) -> None:
        main_pct_label = self.query_one("#cpu_main_pct", Label)
        imu_pct_label = self.query_one("#cpu_imu_pct", Label)
        log_pct_label = self.query_one("#cpu_log_pct", Label)
        apogee_pct_label = self.query_one("#cpu_apogee_pct", Label)
        # cam_pct_label = self.query_one("#cpu_cam_pct", Label)
        main_pct_label.update(f"{self.cpu_usages['Main']:.1f}%")
        imu_pct_label.update(f"{self.cpu_usages['IMU']:.1f}%")
        log_pct_label.update(f"{self.cpu_usages['Log']:.1f}%")
        apogee_pct_label.update(f"{self.cpu_usages['Ap']:.1f}%")
        # cam_pct_label.update(f"{self.cpu_usages['Cam']:.1f}%")

    def update_cpu_bars(self) -> None:
        main_bar = self.query_one("#cpu_main_bar", CPUBars)
        imu_bar = self.query_one("#cpu_imu_bar", CPUBars)
        log_bar = self.query_one("#cpu_log_bar", CPUBars)
        apogee_bar = self.query_one("#cpu_apogee_bar", CPUBars)
        main_bar.update_bars(self.cpu_usages["Main"])
        imu_bar.update_bars(self.cpu_usages["IMU"])
        log_bar.update_bars(self.cpu_usages["Log"])
        apogee_bar.update_bars(self.cpu_usages["Ap"])

    def watch_cpu_usages(self) -> None:
        self.update_labels()
        self.update_cpu_bars()

    def prepare_process_dict(self) -> dict[str, psutil.Process]:
        """
        Prepares a dictionary of processes to monitor CPU usage for.
        :return: A dictionary of process names and their corresponding psutil.Process objects.
        """
        all_processes = {}
        imu_process = self.context.imu._data_fetch_process
        log_process = self.context.logger._log_process
        apogee_process = self.context.apogee_predictor._prediction_process
        # camera_process = self.context.camera.camera_control_process
        current_process = multiprocessing.current_process()
        process_dict = {
            "IMU": imu_process,
            "Log": log_process,
            "Main": current_process,
            "Ap": apogee_process,
            # "Cam": camera_process,
        }
        for k, v in process_dict.items():
            # psutil allows us to monitor CPU usage of a process, along with low level information
            # which we are not using.
            all_processes[k] = psutil.Process(v.pid)
        return all_processes

    def update_cpu_usage(self) -> None:
        """Update CPU usage for each monitored process every `interval` seconds. This is run in
        another thread because polling for CPU usage is a blocking operation."""
        worker = get_current_worker()
        while not worker.is_cancelled:
            for name, process in self.processes.items():
                # interval=None is not recommended and can be inaccurate.
                try:
                    self.cpu_usages.update({name: process.cpu_percent(interval=0.9)})
                except psutil.NoSuchProcess:
                    # The process has ended, so we set the CPU usage to 0.
                    self.cpu_usages.update({name: 0.0})
                    # self.cpu_usages[name] = 0.0
            self.mutate_reactive(CPUUsage.cpu_usages)


class FlightTelemetry(Static):
    """Panel displaying real-time flight information."""

    context: Context
    vertical_velocity = reactive(0.0)
    max_vertical_velocity = reactive(0.0)
    current_height = reactive(0.0)
    max_height = reactive(0.0)
    apogee_prediction = reactive(0.0)
    airbrakes_extension = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Label("Velocity: ", id="vertical_velocity", expand=True)
        yield Label("Max Velocity: ", id="max_vertical_velocity", expand=True)
        yield Label("Altitude: ", id="current_height", expand=True)
        yield Label("Max altitude: ", id="max_height", expand=True)
        yield Label("Predicted Apogee: ", id="apogee_prediction", expand=True)
        yield Label("Airbrakes Extension: ", id="airbrakes_extension", expand=True)
        self.debug_telemetry = DebugTelemetry(id="debug-telemetry")
        self.debug_telemetry.border_title = "DEBUG TELEMETRY"
        yield self.debug_telemetry

    def initialize_widgets(self, context: Context) -> None:
        self.context = context
        self.debug_telemetry.initialize_widgets(context)

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
        self.vertical_velocity = self.context.data_processor.vertical_velocity
        self.max_vertical_velocity = self.context.data_processor.max_vertical_velocity
        self.current_height = self.context.data_processor.current_altitude
        self.max_height = self.context.data_processor.max_altitude
        self.apogee_prediction = self.context.last_apogee_predictor_packet.predicted_apogee
        self.airbrakes_extension = self.context.servo.current_extension.value

        self.debug_telemetry.update_debug_telemetry()
