"""File to handle the downrange distance graphics."""

import numpy as np
from textual.app import ComposeResult
from textual.containers import Center, Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label
from textual_hires_canvas import HiResMode
from textual_plot import PlotWidget

from airbrakes.context import Context
from airbrakes.graphics.utils import InformationStore


class DownrangeMap(Widget):
    """Panel displaying the downrange map."""

    context: Context | None = None
    x_distance: reactive[float] = reactive(0.0)
    y_distance: reactive[float] = reactive(0.0)
    horizontal_range: reactive[float] = reactive(0.0)

    def compose(self) -> ComposeResult:
        with Center():
            yield Label("Downrange Map", id="downrange-map-title")
        self.downrange_plot = PlotWidget(allow_pan_and_zoom=False, id="downrange-map-widget")
        self.downrange_plot._margin_left = 10
        yield self.downrange_plot

        with Center(), Horizontal():
            self.x_distance_label = Label("X Dist:", id="x-distance-label")
            yield self.x_distance_label
            self.y_distance_label = Label("Y Dist:", id="y-distance-label")
            yield self.y_distance_label
            self.horizontal_range_label = Label("Range:", id="horizontal-range-label", expand=True)
            yield self.horizontal_range_label

    def watch_x_distance(self) -> None:
        self.x_distance_label.update(f"X Dist: {self.x_distance:.2f} m")

    def watch_y_distance(self) -> None:
        self.y_distance_label.update(f"Y Dist: {self.y_distance:.2f} m")

    def watch_horizontal_range(self) -> None:
        self.horizontal_range_label.update(f"Range: {self.horizontal_range:.2f} m")

    def initialize_widgets(self, airbrakes: Context) -> None:
        self.context = airbrakes
        self.information_store = InformationStore(time_to_store_for=None)
        self.information_store.initalize_new_data("x_distance")
        self.information_store.initalize_new_data("y_distance")

    def update_plot(self):
        """Updates the information store with the new data."""

        self.information_store.add_data_point("x_distance", self.context.data_processor.x_distance)
        self.information_store.add_data_point("y_distance", self.context.data_processor.y_distance)
        self.x_distance = self.context.data_processor.x_distance
        self.y_distance = self.context.data_processor.y_distance
        self.horizontal_range = self.context.data_processor.horizontal_range

        self.plot_downrange()

    def plot_downrange(self):
        """Plots the downrange map."""
        self.downrange_plot.clear()
        x = np.array(self.information_store.get_data("x_distance"))
        y = np.array(self.information_store.get_data("y_distance"))

        # Scale the plot a bit:
        self.downrange_plot.set_xlimits((np.min(x) * 1.2) - 1, (np.max(x) * 1.2) + 1)
        self.downrange_plot.set_ylimits((np.min(y) * 1.2) - 1, (np.max(y) * 1.2) + 1)

        self.downrange_plot.plot(
            x,
            y,
            line_style="yellow",
            hires_mode=HiResMode.BRAILLE,
        )

        # Plot another line from origin to the current position:
        self.downrange_plot.plot(
            [0, self.x_distance],
            [0, self.y_distance],
            line_style="green",
            hires_mode=HiResMode.BRAILLE,
        )
