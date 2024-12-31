"""Module which has the 2 telemetry panels for the flight display."""

import multiprocessing

import psutil
from textual.app import ComposeResult
from textual.reactive import reactive, var
from textual.widgets import Label, Static, Placeholder
from textual.worker import get_current_worker
from textual_plotext import PlotextPlot

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
        yield CPUUsage(id="cpu_usage_widget")

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes
        self.query_one(CPUUsage).initialize_widgets(airbrakes)

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
            f"Pred. Ap. @ Conv: {self.apogee_at_convergence:.2f} m"
        )

    def watch_log_buffer_size(self) -> None:
        log_buffer_size_label = self.query_one("#log_buffer_size", Label)
        log_buffer_size_label.update(f"Log buffer size: {self.log_buffer_size} packets")

    def watch_fetched_packets(self) -> None:
        fetched_packets_label = self.query_one("#fetched_packets", Label)
        fetched_packets_label.update(f"Fetched packets: {self.fetched_packets}")

    def update_debug_telemetry(self) -> None:
        self.imu_queue_size = self.airbrakes.imu._data_queue.qsize()
        self.log_buffer_size = len(self.airbrakes.logger._log_buffer)
        self.apogee = self.airbrakes.apogee_predictor.apogee
        self.fetched_packets = len(self.airbrakes.imu_data_packets)
        self.state = self.airbrakes.state.name


class CPUBar(Static):
    pass

class CPUBars(Static):
    LIGHT_SHADE = "\u2591" * 5
    MEDIUM_SHADE = "\u2592" * 5
    DARK_SHADE = "\u2593" * 5
    FULL_BLOCK = "\u2588" * 5

    def compose(self) -> ComposeResult:
        """Show 10 CPUBars."""
        for _ in range(10):
            yield CPUBar("")
    
    def update_bars(self, usage: float) -> None:
        """Update the CPUBars with the new usage."""
        # There are 10 bars, so a usage of 10.0 would mean that the first bar
        # is full, and should be changed to FULL_BLOCK.
        # 0 <= usage <= 2.5 -> Use LIGHT_SHADE
        # 2.5 < usage <= 5.0 -> Use MEDIUM_SHADE
        # 5.0 < usage <= 7.5 -> Use DARK_SHADE
        # 7.5 < usage <= 10.0 -> Use FULL_BLOCK
        # The other bars will be nothing (empty).
        # E.g. a usage of 14.5 would mean that the first bar is FULL_BLOCK,
        # the second bar is MEDIUM_SHADE, and the rest are empty.
        # Then we do the same for the next bar, and so on.
        bars = reversed(list(self.children))
        for i, bar in enumerate(bars):
            if usage >= 10.0:
                bar.update(CPUBars.FULL_BLOCK)
                usage -= 10.0
            elif usage >= 7.5:
                bar.update(CPUBars.DARK_SHADE)
                usage -= 2.5
            elif usage >= 5.0:
                bar.update(CPUBars.MEDIUM_SHADE)
                usage -= 2.5
            elif usage >= 2.5:
                bar.update(CPUBars.LIGHT_SHADE)
                usage -= 2.5
            else:
                bar.update(" ")


class CPUUsage(Static):
    """Panel displaying the CPU usage."""

    _airbrakes: AirbrakesContext = None
    cpu_usages = reactive({})

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.processes: dict[str, psutil.Process] = {}
        self.set_reactive(CPUUsage.cpu_usages, {})

    def compose(self) -> ComposeResult:
        # 3x4 grid:
        yield CPUBars(id="cpu_main_bar")
        yield CPUBars(id="cpu_imu_bar")
        yield CPUBars(id="cpu_log_bar")
        yield CPUBars(id="cpu_apogee_bar")
        yield Label("0.00%", id="cpu_main_pct", expand=True)
        yield Label("0.00%", id="cpu_imu_pct", expand=True)
        yield Label("0.00%", id="cpu_log_pct", expand=True)
        yield Label("0.00%", id="cpu_apogee_pct", expand=True)
        yield Label("Main", id="cpu_main_label")
        yield Label("IMU", id="cpu_imu_label")
        yield Label("Log", id="cpu_log_label")
        yield Label("Apogee", id="cpu_apogee_label")
        # yield PlotextPlot(id="cpu_usage_plotext")

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self._airbrakes = airbrakes

    def start(self) -> None:
        self.processes = self.prepare_process_dict()
        self.run_worker(self.update_cpu_usage, name="CPU Polling", thread=True, exclusive=True)
    
    def update_labels(self) -> None:
        main_pct_label = self.query_one("#cpu_main_pct", Label)
        imu_pct_label = self.query_one("#cpu_imu_pct", Label)
        log_pct_label = self.query_one("#cpu_log_pct", Label)
        apogee_pct_label = self.query_one("#cpu_apogee_pct", Label)
        main_pct_label.update(f"{self.cpu_usages['Main']:.2f}%")
        imu_pct_label.update(f"{self.cpu_usages['IMU']:.2f}%")
        log_pct_label.update(f"{self.cpu_usages['Log']:.2f}%")
        apogee_pct_label.update(f"{self.cpu_usages['Ap']:.2f}%")

    def update_cpu_bars(self) -> None:
        main_bar = self.query_one("#cpu_main_bar", CPUBars)
        imu_bar = self.query_one("#cpu_imu_bar", CPUBars)
        log_bar = self.query_one("#cpu_log_bar", CPUBars)
        apogee_bar = self.query_one("#cpu_apogee_bar", CPUBars)
        main_bar.update_bars(self.cpu_usages['Main'])
        imu_bar.update_bars(self.cpu_usages['IMU'])
        log_bar.update_bars(self.cpu_usages['Log'])
        apogee_bar.update_bars(self.cpu_usages['Ap'])

    def watch_cpu_usages(self) -> None:
        self.update_labels()
        self.update_cpu_bars()
        # plt_obj = self.query_one("#cpu_usage_plotext", PlotextPlot)
        # plt = plt_obj.plt
        # plt.clear_data()
        # plt.ylim(0)
        # names = list(self.cpu_usages.keys())
        # names = [name[0].upper() for name in names]
        # values = list(self.cpu_usages.values())
        # plt.bar(names, values, width=0.01, orientation="horizontal")
        # plt.title("CPU Usage")
        # plt_obj.refresh()

    def prepare_process_dict(self) -> dict[str, psutil.Process]:
        """
        Prepares a dictionary of processes to monitor CPU usage for.
        :return: A dictionary of process names and their corresponding psutil.Process objects.
        """
        all_processes = {}
        imu_process = self._airbrakes.imu._data_fetch_process
        log_process = self._airbrakes.logger._log_process
        apogee_process = self._airbrakes.apogee_predictor._prediction_process
        current_process = multiprocessing.current_process()
        process_dict = {"IMU": imu_process, "Log": log_process, "Main": current_process, "Ap": apogee_process}
        for k,v  in process_dict.items():
            # psutil allows us to monitor CPU usage of a process, along with low level information
            # which we are not using.
            all_processes[k] = psutil.Process(v.pid)
        return all_processes

    def update_cpu_usage(self) -> None:
        """Update CPU usage for each monitored process every `interval` seconds. This is run in
        another thread because polling for CPU usage is a blocking operation."""
        cpu_count = psutil.cpu_count()
        worker = get_current_worker()
        while not worker.is_cancelled:
            for name, process in self.processes.items():
                # interval=None is not recommended and can be inaccurate.
                # We normalize the CPU usage by the number of CPUs to get average cpu usage,
                # otherwise it's usually > 100%.
                try:
                    self.cpu_usages.update({name: process.cpu_percent(interval=0.3) / cpu_count})
                    # self.cpu_usages[name] = process.cpu_percent(interval=0.3) / cpu_count
                except psutil.NoSuchProcess:
                    # The process has ended, so we set the CPU usage to 0.
                    self.cpu_usages.update({name: 0.0})
                    # self.cpu_usages[name] = 0.0
            self.mutate_reactive(CPUUsage.cpu_usages)


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
