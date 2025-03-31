"""Module to handle the 2D rocket visualization."""

from textual import on
from textual.app import ComposeResult
from textual.widget import Widget
from textual_hires_canvas import Canvas

from airbrakes.context import Context


class Visualization(Widget):
    """Class to display the 2D rocket visualization."""

    context: Context | None = None

    ROCKET_HEIGHT: int = 15
    """The height of the rocket in cells, at full terminal size."""
    ROCKET_WIDTH: int = 6
    """The width of the rocket in cells, at full terminal size."""

    def compose(self) -> ComposeResult:
        """Compose the main layout, consisting of a canvas."""
        self.canvas = Canvas(50, 100, id="rocket-visualization-canvas")
        yield self.canvas

    def initialize_widgets(self, context: Context) -> None:
        """Initializes the widgets with the context."""
        self.context = context
        # self.draw_rocket_body()

    @on(Canvas.Resize)
    def resize(self, event: Canvas.Resize) -> None:
        """Handle the canvas resize event."""
        self.canvas.reset(size=event.size)
        self.draw_rocket_body()

    def draw_rocket_body(self) -> None:
        """Draw the rectangular rocket body. All other features such as the nosecone, the motor
        are drawn relative to this."""
        # Size of canvas at full terminal size is: 61x37.
        # print(f"Height of the widget: {self.region}")
        # Start at 5,5 and draw the rocket body.
        # The rocket body is a rectangle with the following dimensions:
        #   - Height: ROCKET_HEIGHT
        #   - Width: ROCKET_WIDTH
        #   - Centered in the canvas
        #   - The top left corner is at (5,5)
        #   - The bottom right corner is at (5 + ROCKET_WIDTH, 5 + ROCKET_HEIGHT)
        # The rocket body is drawn in the following way:

        self.canvas.draw_rectangle_box(
            x0=5,
            y0=5,
            x1=5 + self.ROCKET_WIDTH,
            y1=5 + self.ROCKET_HEIGHT,
            thickness=2,
        )
