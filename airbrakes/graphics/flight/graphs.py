"""Module to show various graphs, e.g. altitude, velocity, acceleration, etc."""

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane
from textual_hires_canvas import HiResMode
from textual_plot import PlotWidget

from airbrakes.constants import GRAPH_DATA_STORE_INTERVAL_SECONDS
from airbrakes.context import Context
from airbrakes.graphics.utils import InformationStore
from airbrakes.utils import convert_ns_to_s


class FlightGraph(Widget):
    """Class to display a graph of the data stored in the InformationStore. This is shown
    on the main screen."""

    mode = HiResMode.BRAILLE
    context: Context | None = None
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

    def initialize_widgets(self, context: Context) -> None:
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

        with self.information_store.resize_data() as store:
            store.add_data_point("time", current_flight_time_s)
            store.add_data_point("accel", self.context.data_processor.vertical_acceleration)
            store.add_data_point("vel", self.context.data_processor.vertical_velocity)
            store.add_data_point("alt", self.context.data_processor.current_altitude)
            store.add_data_point(
                "pred_apogee", self.context.last_apogee_predictor_packet.predicted_apogee
            )
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
