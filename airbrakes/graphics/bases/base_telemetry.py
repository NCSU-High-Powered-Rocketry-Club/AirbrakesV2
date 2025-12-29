"""
Base class for the telemetry graphics.

The real flight and mock replay flights will override this class to provide their own telemetry
graphics, while sharing some common functionality.
"""

import abc
from typing import TYPE_CHECKING

from textual.containers import Grid
from textual.reactive import reactive
from textual.widgets import Label, Static

from airbrakes.graphics.utils import set_only_class

if TYPE_CHECKING:
    from textual.app import ComposeResult

    from airbrakes.context import Context


class BaseFlightTelemetry(Static):
    """
    Base class for the telemetry graphics.

    The real flight and mock replay flights will override this class to provide their own telemetry
    graphics, while sharing some common functionality.
    """

    vertical_acceleration = reactive("0.0", init=False)
    max_vertical_acceleration = reactive("0.0", init=False)
    vertical_velocity = reactive("0.0", init=False)
    max_vertical_velocity = reactive("0.0", init=False)
    current_altitude = reactive("0.0", init=False)
    max_altitude = reactive("0.0", init=False)
    airbrakes_extension = reactive("0.0", init=False)

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
        self.accel_label = Label("0.0", id="vertical-acceleration-label", expand=True)
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
        self.velocity_label = Label("0.0", id="vertical-velocity-label", expand=True)
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
        self.altitude_label = Label("0.0", id="current-altitude-label", expand=True)
        yield self.altitude_label
        yield Static("Max:", id="max-altitude-static-label")
        self.max_altitude_label = Label("0.0", id="max-altitude-label", expand=True)
        yield self.max_altitude_label
        yield Static("m", id="altitude-units-static-label", classes="units")

    def _compose_airbrakes_extension_label(self) -> ComposeResult:
        """
        Called by superclass to compose the airbrakes extension label.
        """
        yield Static("Airbrakes Extension:", id="airbrakes-extension-static-label")
        self.airbrakes_label = Label("0.0", id="airbrakes-extension-label", expand=True)
        yield self.airbrakes_label
        yield Static()
        yield Static()
        yield Static("\u00b0", id="airbrakes-extension-units-static-label", classes="units")

    def watch_vertical_acceleration(self) -> None:
        self.accel_label.update(self.vertical_acceleration)

    def watch_max_vertical_acceleration(self) -> None:
        self.max_accel_label.update(self.max_vertical_acceleration)

    def watch_vertical_velocity(self) -> None:
        self.velocity_label.update(self.vertical_velocity)

    def watch_max_vertical_velocity(self) -> None:
        self.max_velocity_label.update(self.max_vertical_velocity)

    def watch_current_altitude(self) -> None:
        self.altitude_label.update(self.current_altitude)

    def watch_max_altitude(self) -> None:
        self.max_altitude_label.update(self.max_altitude)

    def watch_airbrakes_extension(self) -> None:
        self.airbrakes_label.update(self.airbrakes_extension)

    def update_telemetry(self) -> None:
        """
        Base method to update the telemetry.

        This method should be overridden by the subclasses to provide their own implementation.
        """
        self.vertical_acceleration = f"{self.context.data_processor.vertical_acceleration:.2f}"
        self.current_altitude = f"{self.context.data_processor.current_altitude:.2f}"
        self.max_altitude = f"{self.context.data_processor.max_altitude:.2f}"
        self.vertical_velocity = f"{self.context.data_processor.vertical_velocity:.2f}"
        self.max_vertical_velocity = f"{self.context.data_processor.max_vertical_velocity:.2f}"
        self.airbrakes_extension = f"{self.context.servo.current_extension.value:.2f}"


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
        self.pitch_label = Label("0.0", id="average-pitch-label", expand=True)
        yield self.pitch_label
        yield Static("\u00b0", id="pitch-units", classes="units")

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
        else:
            self.invalid_fields_label.remove_class("bad-data")

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
