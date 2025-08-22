"""
Telemetry widget to show real time data from the sensors.
"""

from textual.app import ComposeResult
from textual.containers import Grid
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Label, Static

from airbrakes.context import Context
from airbrakes.graphics.bases.base_telemetry import (
    BaseDebugTelemetry,
    BaseFlightTelemetry,
    BaseQueueSizesTelemetry,
    CPUUsage,
)
from airbrakes.graphics.screens.launcher import RealLaunchOptions
from airbrakes.graphics.utils import set_only_class


class BadDataSignal(Message):
    """
    Message to signal that the data is bad.

    This will change the flight header to NO GO and sound the alarm.
    """


class GoodDataSignal(Message):
    """
    Message to signal that the data is good.

    This will change the flight header to GO FOR LAUNCH and stop the alarm.
    """


class RealFlightTelemetry(BaseFlightTelemetry):
    """
    Panel displaying real-time flight information.
    """

    __slots__ = ("bad_velocity",)

    def compose(self) -> ComposeResult:
        with Grid(id="real-flight-telemetry-grid"):  # Declared with 5 columns in tcss file
            # Row 1:
            yield from self._compose_vertical_acceleration_label()
            # Row 2:
            yield from self._compose_vertical_velocity_label()
            # Row 3:
            yield from self._compose_current_altitude_label()
            # Row 4:
            yield from self._compose_airbrakes_extension_label()

        self.debug_telemetry = RealDebugTelemetry(id="real-debug-telemetry")
        self.debug_telemetry.border_title = "DEBUG TELEMETRY"
        yield self.debug_telemetry

    def initialize_widgets(self, context: Context, launch_options: RealLaunchOptions) -> None:
        """
        Supplies the airbrakes context and related objects to the widgets for proper operation.
        """
        super().initialize_widgets(context, launch_options)
        self.debug_telemetry.initialize_widgets(context, launch_options)
        self.bad_velocity = False

        if not launch_options.verbose:
            self.max_accel_label.disabled = True
            self.query_one("#max-vertical-acceleration-static-label").disabled = True

    def watch_vertical_velocity(self) -> None:
        """
        Watches the vertical velocity and updates the label.
        """
        super().watch_vertical_velocity()
        # Check if the vertical velocity is bad:
        bad_velocity = float(self.vertical_velocity) < -2.0
        if bad_velocity and not self.bad_velocity:
            set_only_class(self.velocity_label, "bad-data")
            self.post_message(BadDataSignal())
            self.bad_velocity = True
            return

        # If the vertical velocity is good, remove the bad-data class:
        if not bad_velocity and self.bad_velocity:
            self.bad_velocity = False
            self.velocity_label.remove_class("bad-data")
            self.post_message(GoodDataSignal())

    def update_telemetry(self) -> None:
        super().update_telemetry()
        self.debug_telemetry.update_telemetry()


class RealDebugTelemetry(BaseDebugTelemetry):
    """
    Panel displaying real-time debug information.
    """

    encoder_position: reactive[int] = reactive(0, init=False)

    __slots__ = ("encoder_position_label", "queue_sizes_widget")
    bad_pitch: bool = False
    has_invalid_fields: bool = False
    initial_pitch: float | None = None

    def compose(self) -> ComposeResult:
        with Grid(id="real-debug-telemetry-grid"):  # Declared with 3 columns in tcss file
            # Row 1:
            yield from self._compose_invalid_fields_label()
            # Row 2:
            yield from self._compose_average_pitch_label()

            # Row 3:
            yield Static("Encoder Position:", id="encoder-position-static-label")
            self.encoder_position_label = Label("0", id="encoder-position-label")
            yield self.encoder_position_label

        # Buttons for extending/retracting the airbrakes:
        self.extend_airbrakes_button = Button(
            "[u]E[/]xtend Airbrakes",
            id="extend-airbrakes-button",
            variant="success",
        )
        self.retract_airbrakes_button = Button(
            "[u]R[/]etract Airbrakes",
            id="retract-airbrakes-button",
            variant="error",
        )
        yield self.extend_airbrakes_button
        yield self.retract_airbrakes_button

        self.queue_sizes_widget = RealQueueSizesTelemetry(id="real-queue-size-telemetry")
        yield self.queue_sizes_widget

        yield from self._compose_cpu_usage_widget()

    def start(self) -> None:
        """
        Starts updating the CPU usage panel.
        """
        self.query_one(CPUUsage).start()

    def stop(self) -> None:
        """
        Stops updating the CPU usage panel.
        """
        self.query_one(CPUUsage).stop()

    def initialize_widgets(self, context: Context, launch_options: RealLaunchOptions) -> None:
        """
        Supplies the airbrakes context and related objects to the widgets for proper operation.
        """
        super().initialize_widgets(context)
        self.queue_sizes_widget.initialize_widgets(context)
        # Disable the CPU usage monitor and buttons if not running with -v:
        if not launch_options.verbose:
            self.query_one(CPUUsage).disabled = True
            self.extend_airbrakes_button.disabled = True
            self.retract_airbrakes_button.disabled = True

    def watch_encoder_position(self) -> None:
        """
        Watches the encoder position and updates the label.
        """
        self.encoder_position_label.update(str(self.encoder_position))

    def watch_average_pitch(self) -> None:
        super().watch_average_pitch()

        if self.initial_pitch is None:
            # If the initial pitch is not set, set it to the current average pitch:
            self.initial_pitch = self.average_pitch

        # Check if the average pitch is bad:
        pitch_is_bad = abs(self.average_pitch - self.initial_pitch) > 2.0

        if pitch_is_bad and not self.bad_pitch:
            set_only_class(self.pitch_label, "bad-data")
            self.post_message(BadDataSignal())
            self.bad_pitch = True
            return

        # If the average pitch is good, remove the bad-data class:
        if not pitch_is_bad and self.bad_pitch:
            self.bad_pitch = False
            self.pitch_label.remove_class("bad-data")
            self.post_message(GoodDataSignal())

    def watch_invalid_fields(self) -> None:
        super().watch_invalid_fields()

        # Check if the invalid fields are bad:
        if self.invalid_fields and not self.has_invalid_fields:
            self.post_message(BadDataSignal())
            self.has_invalid_fields = True
            return

        # If the invalid fields are good, remove the bad-data class:
        if not self.invalid_fields and self.has_invalid_fields:
            self.has_invalid_fields = False
            self.post_message(GoodDataSignal())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "extend-airbrakes-button":
            self.context.extend_airbrakes()
        elif event.button.id == "retract-airbrakes-button":
            self.context.retract_airbrakes()

    def update_telemetry(self) -> None:
        super().update_telemetry()
        self.queue_sizes_widget.update_queue_sizes_telemetry()
        self.encoder_position = self.context.servo_data_packet.encoder_position


class RealQueueSizesTelemetry(BaseQueueSizesTelemetry):
    """
    Panel displaying the queue sizes for the telemetry data.
    """

    __slots__ = ()
    bad_queue_size: bool = False

    def watch_imu_packets_per_cycle(self) -> None:
        super().watch_imu_packets_per_cycle()

        high_packets_per_cycle = self.imu_packets_per_cycle > 30
        if high_packets_per_cycle and not self.bad_queue_size:
            set_only_class(self.imu_packets_per_cycle_label, "bad-data")
            self.post_message(BadDataSignal())
            self.bad_queue_size = True
            return

        # If the IMU packets per cycle is good, remove the bad-data class:
        if not high_packets_per_cycle and self.bad_queue_size:
            self.bad_queue_size = False
            self.imu_packets_per_cycle_label.remove_class("bad-data")
            self.post_message(GoodDataSignal())
