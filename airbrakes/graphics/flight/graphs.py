"""Module to show various graphs, e.g. altitude, velocity, acceleration, etc."""

from collections import deque

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import TabbedContent, TabPane
from textual_hires_canvas import HiResMode
from textual_plot import PlotWidget

from airbrakes.constants import GRAPH_DATA_STORE_INTERVAL_SECONDS
from airbrakes.context import AirbrakesContext
from airbrakes.utils import convert_seconds_to_packets


class InformationStore:
    """Class to store the information to be displayed in the graphs. A set amount of time's
    worth of data is stored as a rolling buffer. This class is independent of the GUI, because
    it is meant to be extensible and reusable, for example for use in scripts, to show other IMU
    data."""

    def __init__(
        self, time_to_store_for: float, raw_packet_freq: float, est_packet_freq: float
    ) -> None:
        self.packets_to_store: int = convert_seconds_to_packets(
            time_to_store_for, raw_packet_freq, est_packet_freq
        )

        self.data: dict[str, deque[float]] = {}

    def initalize_new_data(self, data_name: str) -> None:
        """Initializes a new data set to store in the buffer.

        :param data_name: The name of the data to store.
        """
        self.data[data_name] = deque(maxlen=self.packets_to_store)

    def add_single_data_point(self, data_name: str, data: float) -> None:
        """Adds data to the buffer.

        :param data_name: The name of the data to store.
        :param data: The data to store.
        """
        self.data[data_name].append(data)

    def add_multiple_data_points(self, data_name: str, data: list[float]) -> None:
        """Adds multiple data points to the buffer.

        :param data_name: The name of the data to store.
        :param data: The data to store.
        """
        self.data[data_name].extend(data)

    def get_data(self, data_name: str) -> deque[float]:
        """Returns the data stored in the buffer.

        :param data_name: The name of the data to return.
        """
        return self.data[data_name]


class MainGraph(ScrollableContainer):
    """Class to display a graph of the data stored in the InformationStore. This is shown
    on the main screen."""

    mode = HiResMode.BRAILLE
    context: AirbrakesContext | None = None
    information_store: InformationStore | None = None

    def compose(self) -> ComposeResult:
        """Compose the main layout, consisting of 3 tabs."""
        with TabbedContent():
            with TabPane("Acceleration"):
                self.accel_plot = PlotWidget()
                yield self.accel_plot
            with TabPane("Velocity"):
                self.vel_plot = PlotWidget()
                yield self.vel_plot
            with TabPane("Altitude"):
                self.alt_plot = PlotWidget()
                yield self.alt_plot
            with TabPane("Predicted Apogee"):
                self.apogee_plot = PlotWidget()
                yield self.apogee_plot

    def initialize_widgets(self, context: AirbrakesContext) -> None:
        """Initializes the widgets with the context."""
        self.context = context
        self.information_store = InformationStore(
            time_to_store_for=GRAPH_DATA_STORE_INTERVAL_SECONDS,
            raw_packet_freq=self.context.imu.file_metadata["imu_details"]["raw_packet_freqeuncy"],
            est_packet_freq=self.context.imu.file_metadata["imu_details"]["est_packet_freqeuncy"],
        )
        self.information_store.initalize_new_data("accel")
        self.information_store.initalize_new_data("vel")
        self.information_store.initalize_new_data("alt")
        self.information_store.initalize_new_data("pred_apogee")

    def update_graphs(self) -> None:
        """Update the information stores with the latest data."""
        # TODO: If our display update frequency is higher than sim speed, we risk adding the same
        # data multiple times. We should add a check to see if the data is new before adding it.

        # self.information_store.
