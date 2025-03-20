"""Module to show various graphs, e.g. altitude, velocity, acceleration, etc."""

import bisect

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane
from textual_hires_canvas import HiResMode
from textual_plot import PlotWidget

from airbrakes.constants import GRAPH_DATA_STORE_INTERVAL_SECONDS
from airbrakes.context import AirbrakesContext
from airbrakes.utils import convert_ns_to_s


class InformationStore:
    """Class to store the information to be displayed in the graphs. A set amount of time's
    worth of data is stored as a rolling buffer. This class is independent of the GUI, because
    it is meant to be extensible and reusable, for example for use in scripts, to show other IMU
    data."""

    __slots__ = ("data", "time_to_store_for")

    def __init__(self, time_to_store_for: float) -> None:
        self.time_to_store_for = time_to_store_for
        self.data: dict[str, list[float]] = {}

    def initalize_new_data(self, data_name: str) -> None:
        """Initializes a new data set to store in the buffer.

        :param data_name: The name of the data to store.
        """
        self.data[data_name] = []

    def add_data_point(self, data_name: str, data: float) -> None:
        """Adds data to the buffer.

        :param data_name: The name of the data to store.
        :param data: The data to store.
        """
        self.data[data_name].append(data)

    def get_data(self, data_name: str) -> list[float]:
        """Returns the data stored in the buffer.

        :param data_name: The name of the data to return.
        """
        return self.data[data_name]

    def resize_data(self) -> None:
        """Trims the data if the time difference between the first and last data points is greater
        than the time to store for."""
        # TODO: Make a context manager to avoid calling this function every time
        # TODO: Benchmark the numpy approach
        last_time = self.data["time"][-1]
        min_time = last_time - self.time_to_store_for
        min_time_index = bisect.bisect_left(self.data["time"], min_time)

        for data_name in self.data:
            self.data[data_name] = self.data[data_name][min_time_index:]


class FlightGraph(Widget):
    """Class to display a graph of the data stored in the InformationStore. This is shown
    on the main screen."""

    mode = HiResMode.BRAILLE
    context: AirbrakesContext | None = None
    information_store: InformationStore | None = None

    def compose(self) -> ComposeResult:
        """Compose the main layout, consisting of 3 tabs."""
        self.tabbed_content = TabbedContent(id="tabbed-content", initial="accel-tab", disabled=True)
        with self.tabbed_content:
            with TabPane("Acceleration", id="accel-tab"):
                self.accel_plot = PlotWidget(allow_pan_and_zoom=False)
                self.accel_plot._margin_left = 5
                yield self.accel_plot
            with TabPane("Velocity", id="vel-tab"):
                self.vel_plot = PlotWidget(allow_pan_and_zoom=False)
                self.vel_plot._margin_left = 5
                yield self.vel_plot
            with TabPane("Altitude", id="alt-tab"):
                self.alt_plot = PlotWidget(allow_pan_and_zoom=False)
                self.alt_plot._margin_left = 5
                yield self.alt_plot
            with TabPane("Predicted Apogee", id="pred-apogee-tab"):
                self.apogee_plot = PlotWidget(allow_pan_and_zoom=False)
                self.apogee_plot._margin_left = 5
                yield self.apogee_plot

    def initialize_widgets(self, context: AirbrakesContext) -> None:
        """Initializes the widgets with the context."""
        self.context = context
        self.information_store = InformationStore(
            time_to_store_for=GRAPH_DATA_STORE_INTERVAL_SECONDS,
        )
        self.information_store.initalize_new_data("accel")
        self.information_store.initalize_new_data("vel")
        self.information_store.initalize_new_data("alt")
        self.information_store.initalize_new_data("pred_apogee")
        self.information_store.initalize_new_data("time")
        self.tabbed_content.disabled = False

    def update_data(self, current_flight_time_ns: int) -> None:
        """Update the graphs (i.e. add data) when the time since launch changes."""
        current_flight_time_s: float = convert_ns_to_s(current_flight_time_ns)
        self.information_store.add_data_point("time", current_flight_time_s)
        self.information_store.add_data_point(
            "accel", self.context.data_processor.vertical_acceleration
        )
        self.information_store.add_data_point("vel", self.context.data_processor.vertical_velocity)
        self.information_store.add_data_point("alt", self.context.data_processor.current_altitude)
        self.information_store.add_data_point(
            "pred_apogee", self.context.last_apogee_predictor_packet.predicted_apogee
        )
        self.information_store.resize_data()
        # Call the currently active tab's function:
        active_pane = self.tabbed_content.active_pane
        if active_pane.id == "accel-tab":
            self.plot_acceleration()
        elif active_pane.id == "vel-tab":
            self.plot_velocity()
        elif active_pane.id == "alt-tab":
            self.plot_altitude()
        elif active_pane.id == "pred-apogee-tab":
            self.plot_predicted_apogee()
        else:
            return

    @on(TabbedContent.TabActivated, pane="#accel-tab")
    def accel_tab_switch(self) -> None:
        """Show the acceleration graph when the acceleration tab is activated."""
        if self.information_store is not None:
            self.plot_acceleration()

    @on(TabbedContent.TabActivated, pane="#vel-tab")
    def vel_tab_switch(self) -> None:
        """Show the velocity graph when the velocity tab is activated."""
        if self.information_store is not None:
            self.plot_velocity()

    @on(TabbedContent.TabActivated, pane="#alt-tab")
    def alt_tab_switch(self) -> None:
        """Show the altitude graph when the altitude tab is activated."""
        if self.information_store is not None:
            self.plot_altitude()

    @on(TabbedContent.TabActivated, pane="#pred-apogee-tab")
    def apogee_tab_switch(self) -> None:
        """Show the predicted apogee graph when the predicted apogee tab is activated."""
        if self.information_store is not None:
            self.plot_predicted_apogee()

    def plot_acceleration(self) -> None:
        """Plot the acceleration graph when the acceleration tab is activated."""
        plot = self.accel_plot
        y = self.information_store.get_data("accel")
        line_color = "red"
        plot.clear()
        x = self.information_store.get_data("time")
        plot.plot(x, y, line_style=line_color, hires_mode=self.mode)

    def plot_velocity(self) -> None:
        """Plot the velocity graph when the velocity tab is activated."""
        plot = self.vel_plot
        y = self.information_store.get_data("vel")
        line_color = "blue"
        plot.clear()
        x = self.information_store.get_data("time")
        plot.plot(x, y, line_style=line_color, hires_mode=self.mode)

    def plot_altitude(self) -> None:
        """Plot the altitude graph when the altitude tab is activated."""
        plot = self.alt_plot
        y = self.information_store.get_data("alt")
        line_color = "green"
        plot.clear()
        x = self.information_store.get_data("time")
        plot.plot(x, y, line_style=line_color, hires_mode=self.mode)

    def plot_predicted_apogee(self) -> None:
        """Plot the predicted apogee graph when the predicted apogee tab is activated."""
        plot = self.apogee_plot
        y = self.information_store.get_data("pred_apogee")
        line_color = "purple"
        plot.clear()
        x = self.information_store.get_data("time")
        plot.plot(x, y, line_style=line_color, hires_mode=self.mode)
