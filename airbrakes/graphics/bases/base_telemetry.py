"""
Base class for the telemetry graphics.

The real flight and mock replay flights will override this class to provide their own telemetry
graphics, while sharing some common functionality.
"""

import abc
import multiprocessing

import psutil
from textual.app import ComposeResult
from textual.containers import Grid
from textual.reactive import reactive
from textual.widgets import Label, Static
from textual.worker import Worker, get_current_worker

from airbrakes.context import Context
from airbrakes.graphics.utils import set_only_class


class BaseFlightTelemetry(Static):
    """
    Base class for the telemetry graphics.

    The real flight and mock replay flights will override this class to provide their own telemetry
    graphics, while sharing some common functionality.
    """

    vertical_acceleration = reactive(0.0, init=False)
    max_vertical_acceleration = reactive(0.0, init=False)
    vertical_velocity = reactive(0.0, init=False)
    max_vertical_velocity = reactive(0.0, init=False)
    current_altitude = reactive(0.0, init=False)
    max_altitude = reactive(0.0, init=False)
    airbrakes_extension = reactive(0.0, init=False)

    __slots__ = (
        "accel_label",
        "airbrakes_label",
        "altitude_label",
        "context",
        "max_accel_label",
        "max_altitude_label",
        "max_velocity_label",
        "velocity_label",
    )

    @abc.abstractmethod
    def compose(self) -> ComposeResult: ...

    def initialize_widgets(self, context: Context, *_, **__) -> None:
        self.context = context

    def _compose_vertical_acceleration_label(self) -> ComposeResult:
        """
        Called by superclass to compose the vertical acceleration label.
        """
        yield Static("Vertical Accel:", id="vertical-acceleration-static-label")
        self.accel_label = Label("0.0", id="vertical-acceleration-label")
        yield self.accel_label
        yield Static("Max:", id="max-vertical-acceleration-static-label")
        self.max_accel_label = Label("0.0", id="max-vertical-acceleration-label")
        yield self.max_accel_label
        yield Static("m/s\u00b2", id="vertical-acceleration-units-static-label", classes="units")

    def _compose_vertical_velocity_label(self) -> ComposeResult:
        """
        Called by superclass to compose the vertical velocity label.
        """
        yield Static("Vertical Velocity:", id="vertical-velocity-static-label")
        self.velocity_label = Label("0.0", id="vertical-velocity-label")
        yield self.velocity_label
        yield Static("Max:", id="max-vertical-velocity-static-label")
        self.max_velocity_label = Label("0.0", id="max-vertical-velocity-label")
        yield self.max_velocity_label
        yield Static("m/s", id="vertical-velocity-units-static-label", classes="units")

    def _compose_current_altitude_label(self) -> ComposeResult:
        """
        Called by superclass to compose the current altitude label.
        """
        yield Static("Altitude:", id="altitude-static-label")
        self.altitude_label = Label("0.0", id="current-altitude-label")
        yield self.altitude_label
        yield Static("Max:", id="max-altitude-static-label")
        self.max_altitude_label = Label("0.0", id="max-altitude-label")
        yield self.max_altitude_label
        yield Static("m", id="altitude-units-static-label", classes="units")

    def _compose_airbrakes_extension_label(self) -> ComposeResult:
        """
        Called by superclass to compose the airbrakes extension label.
        """
        yield Static("Airbrakes Extension:", id="airbrakes-extension-static-label")
        self.airbrakes_label = Label("0.0", id="airbrakes-extension-label")
        yield self.airbrakes_label
        yield Static()
        yield Static()
        yield Static("\u00b0", id="airbrakes-extension-units-static-label", classes="units")

    def watch_vertical_acceleration(self) -> None:
        self.accel_label.update(f"{self.vertical_acceleration:.2f}")

    def watch_max_vertical_acceleration(self) -> None:
        self.max_accel_label.update(f"{self.max_vertical_acceleration:.2f}")

    def watch_vertical_velocity(self) -> None:
        self.velocity_label.update(f"{self.vertical_velocity:.2f}")

    def watch_max_vertical_velocity(self) -> None:
        self.max_velocity_label.update(f"{self.max_vertical_velocity:.2f}")

    def watch_current_altitude(self) -> None:
        self.altitude_label.update(f"{self.current_altitude:.2f}")

    def watch_max_altitude(self) -> None:
        self.max_altitude_label.update(f"{self.max_altitude:.2f}")

    def watch_airbrakes_extension(self) -> None:
        self.airbrakes_label.update(f"{self.airbrakes_extension:.2f}")

    def update_telemetry(self) -> None:
        """
        Base method to update the telemetry.

        This method should be overridden by the subclasses to provide their own implementation.
        """
        self.vertical_acceleration = self.context.data_processor.vertical_acceleration
        self.current_altitude = self.context.data_processor.current_altitude
        self.max_altitude = self.context.data_processor.max_altitude
        self.vertical_velocity = self.context.data_processor.vertical_velocity
        self.max_vertical_velocity = self.context.data_processor.max_vertical_velocity
        self.airbrakes_extension = self.context.servo.current_extension.value


class BaseDebugTelemetry(Static):
    """
    Base class for the telemetry graphics.

    The real flight and mock replay flights will override this class to provide their own telemetry
    graphics, while sharing some common functionality.
    """

    average_pitch = reactive(0.0, init=False)
    invalid_fields = reactive("", init=False)

    __slots__ = (
        "context",
        "invalid_fields_label",
        "pitch_label",
    )

    @abc.abstractmethod
    def compose(self) -> ComposeResult: ...

    def initialize_widgets(self, context: Context, *_, **__) -> None:
        """
        Initialize the widgets with the flight data from the context.
        """
        self.context = context
        self.query_one(CPUUsage).initialize_widgets(context)

    def _compose_invalid_fields_label(self) -> ComposeResult:
        """
        Called by superclass to compose the invalid fields label.
        """
        yield Static("Invalid fields:", id="invalid-fields-static-label")
        self.invalid_fields_label = Label(
            "None", id="invalid-fields-label", markup=False, expand=True
        )
        yield self.invalid_fields_label

    def _compose_average_pitch_label(self) -> ComposeResult:
        """
        Called by superclass to compose the average pitch label.
        """
        yield Static("Average Pitch:", id="average-pitch-static-label")
        self.pitch_label = Label("0.0", id="average-pitch-label")
        yield self.pitch_label
        yield Static("\u00b0", id="pitch-units", classes="units")

    def _compose_cpu_usage_widget(self) -> ComposeResult:
        """
        Called by superclass to compose the CPU usage widget.
        """
        cpu_usage = CPUUsage(id="cpu-usage-widget")
        cpu_usage.border_title = "CPU Usage"
        yield cpu_usage

    def watch_average_pitch(self) -> None:
        """
        Update the average pitch label with the new value.

        The label is defined in a superclass.
        """
        self.pitch_label.update(f"{self.average_pitch:.2f}")

    def watch_invalid_fields(self) -> None:
        """
        Update the invalid fields label with the new value.

        The label is defined in a superclass.
        """
        if self.invalid_fields:
            set_only_class(self.invalid_fields_label, "bad-data")

        self.invalid_fields_label.update(f"{self.invalid_fields}")

    def update_telemetry(self) -> None:
        """
        Update the debug telemetry.
        """
        self.invalid_fields = self.context.data_processor._last_data_packet.invalid_fields
        self.average_pitch = self.context.data_processor.average_pitch


class BaseQueueSizesTelemetry(Static):
    """
    Class to display the queue sizes of the queues throughout the application.
    """

    __slots__ = (
        "imu_packets_per_cycle_label",
        "log_buffer_size_label",
        "queued_packets_label",
        "retrieved_packets_label",
    )

    queued_imu_packets = reactive(0, init=False)
    log_buffer_size = reactive(0, init=False)
    retrieved_packets = reactive(0, init=False)
    imu_packets_per_cycle = reactive(0, init=False)

    def compose(self) -> ComposeResult:
        with Grid(id="packet-grid") as grid:  # Declared with 4 columns in tcss file
            # Row 1:
            self.imu_packets_per_cycle_label = Label("0", id="imu-packets-per-cycle-label")
            yield self.imu_packets_per_cycle_label
            self.queued_packets_label = Label("0", id="queued-imu-packets-label")
            yield self.queued_packets_label
            self.retrieved_packets_label = Label("0", id="retrieved-packets-label")
            yield self.retrieved_packets_label
            self.log_buffer_size_label = Label("0", id="log-buffer-size")
            yield self.log_buffer_size_label

            # Row 2:
            yield Static("Hardware", id="hardware-static-label")
            yield Static("IMU", id="imu-static-label")
            yield Static("Main", id="main-static-label")
            yield Static("Log Buffer", id="log-buffer-static-label")

            # Assign the title to the grid:
            grid.border_title = "Queue Sizes"

    def initialize_widgets(self, context: Context) -> None:
        """
        Initialize the widgets with the flight data from the context.
        """
        self.context = context

    def watch_queued_imu_packets(self) -> None:
        self.queued_packets_label.update(f"{self.queued_imu_packets}")

    def watch_log_buffer_size(self) -> None:
        self.log_buffer_size_label.update(f"{self.log_buffer_size}")

    def watch_retrieved_packets(self) -> None:
        self.retrieved_packets_label.update(f"{self.retrieved_packets}")

    def watch_imu_packets_per_cycle(self) -> None:
        self.imu_packets_per_cycle_label.update(f"{self.imu_packets_per_cycle}")

    def update_queue_sizes_telemetry(self) -> None:
        """
        Update the queue sizes telemetry.
        """
        self.imu_packets_per_cycle = self.context.imu.imu_packets_per_cycle
        self.queued_imu_packets = self.context.context_data_packet.queued_imu_packets
        self.retrieved_packets = self.context.context_data_packet.retrieved_imu_packets
        self.log_buffer_size = len(self.context.logger._log_buffer)


class CPUUsage(Static):
    """
    Panel displaying the CPU usage.
    """

    cpu_usages = reactive({})

    __slots__ = ("context", "processes", "worker")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.processes: dict[str, psutil.Process] = {}
        self.set_reactive(CPUUsage.cpu_usages, {})
        self.worker: Worker = None
        self.context: Context | None = None

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
        if self.worker:
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
        """
        Update CPU usage for each monitored process every `interval` seconds.

        This is run in another thread because polling for CPU usage is a blocking operation.
        """
        worker = get_current_worker()
        while not worker.is_cancelled:
            for name, process in self.processes.items():
                # interval=None is not recommended and can be inaccurate.
                try:
                    self.cpu_usages.update({name: process.cpu_percent(interval=0.9)})
                except psutil.NoSuchProcess:
                    # The process has ended, so we set the CPU usage to 0.
                    self.cpu_usages.update({name: 0.0})
            self.mutate_reactive(CPUUsage.cpu_usages)


class CPUBars(Static):
    """
    Represents a group of CPU bars.
    """

    LIGHT_SHADE = "\u2591" * 5
    MEDIUM_SHADE = "\u2592" * 5
    DARK_SHADE = "\u2593" * 5
    FULL_BLOCK = "\u2588" * 5

    __slots__ = ()

    def compose(self) -> ComposeResult:
        """
        Show 10 CPUBars.
        """
        for _ in range(10):
            bar = CPUBar(CPUBars.LIGHT_SHADE)
            bar.set_class(True, "inactive")
            yield bar

    def update_bars(self, usage: float) -> None:
        """
        Update the CPUBars with the new usage.
        """
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


class CPUBar(Static):
    """
    Represents a single CPU bar.
    """

    __slots__ = ()
