"""File to handle the downrange distance graphics."""

from textual.app import ComposeResult
from textual.widgets import Label, Static

from airbrakes.context import AirbrakesContext


class DownrangeMap(Static):
    """Panel displaying the downrange map."""

    airbrakes: AirbrakesContext | None = None

    def __init__(self) -> None:
        super().__init__()
        self.downrange_distance: DownrangeDistance = DownrangeDistance()

    def compose(self) -> ComposeResult:
        yield Label("Downrange Map")

    def initialize_widgets(self, airbrakes: AirbrakesContext) -> None:
        self.airbrakes = airbrakes


class DownrangeDistance:
    """Regular class to handle the downrange distance calculations."""

    def __init__(self) -> None:
        self.downrange_distance: float = 0.0

    def calculate_downrange_distance(self) -> None:
        """Calculates the downrange distance."""

    def update_downrange_distance(self) -> None:
        """Updates the downrange distance."""
