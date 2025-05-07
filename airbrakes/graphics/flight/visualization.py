"""
Module to handle the 2D rocket visualization.
"""

import numpy as np
from textual import on
from textual._box_drawing import combine_quads
from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual_hires_canvas import Canvas
from textual_hires_canvas.canvas import get_box

from airbrakes.constants import ServoExtension
from airbrakes.context import Context

# Constants for rocket dimensions (in canvas cells)
ROCKET_WIDTH = 6
ROCKET_HEIGHT = 15
NOSECONE_HEIGHT = 5
ASPECT_RATIO = 0.5  # Terminal cell width-to-height ratio (roughly)
NOZZLE_HEIGHT = 2  # Height of the nozzle in cells
NOZZLE_WIDTH = ROCKET_WIDTH / 2.0  # Width of the nozzle in cells
FLAME_OFFSETS = [0.5, 1, 1.5, 2, 2.5, 3]  # Distances in cells where "X" flames will appear
AIRBRAKE_LENGTH = 2  # Length of airbrakes in cells

# Constants for altitude axis
# NUM_TICKS = 5
TICK_INTERVAL = 1.7  # meters per tick  (NOT TO SCALE)
# TICK_SPACING = 10  # cells between ticks
AXIS_X = 0  # x-position of the axis
METERS_PER_CELL = 0.15  # Meters per canvas cell (defines scale)


class Visualization(Widget):
    """
    Class to display the 2D rocket visualization.
    """

    context: Context | None = None
    pitch: reactive[float] = reactive(0.0, init=False)
    state: reactive[str] = reactive("StandbyState", init=False)
    extension: reactive[float] = reactive(ServoExtension.MIN_EXTENSION.value, init=False)
    altitude: reactive[float] = reactive(0.0, init=False)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.original_points = []
        self.cx: float = 0.0
        self.cy: float = 0.0
        self.pitch_at_last_draw: float = 0.0
        self.altitude_at_last_draw: float = 0.0
        self.is_motor_burning: bool = False
        self.is_airbrakes_deployed: bool = False

    def compose(self) -> ComposeResult:
        """
        Compose the main layout with an initialized canvas.
        """
        self.canvas = Canvas(50, 100, id="rocket-visualization-canvas")
        yield self.canvas

    def initialize_canvas(self, width: int, height: int) -> None:
        """
        Initialize the rocket geometry.
        """
        self.cx = width / 2.0
        self.cy = height / 2.0
        scaling_factor = 1 / ASPECT_RATIO  # e.g., 1 / 0.5 = 2
        # Existing points
        base_left = (self.cx - ROCKET_WIDTH / 2.0, (self.cy + ROCKET_HEIGHT / 2.0) * scaling_factor)
        base_right = (
            self.cx + ROCKET_WIDTH / 2.0,
            (self.cy + ROCKET_HEIGHT / 2.0) * scaling_factor,
        )
        nose_left = (self.cx - ROCKET_WIDTH / 2.0, (self.cy - ROCKET_HEIGHT / 2.0) * scaling_factor)
        nose_right = (
            self.cx + ROCKET_WIDTH / 2.0,
            (self.cy - ROCKET_HEIGHT / 2.0) * scaling_factor,
        )
        nose_tip = (self.cx, (self.cy - ROCKET_HEIGHT / 2.0 - NOSECONE_HEIGHT) * scaling_factor)

        # New nozzle points (trapezoid approximating a rounded shape)
        nozzle_top_left = (
            self.cx - NOZZLE_WIDTH / 2.0,
            (self.cy + ROCKET_HEIGHT / 2.0) * scaling_factor,
        )
        nozzle_top_right = (
            self.cx + NOZZLE_WIDTH / 2.0,
            (self.cy + ROCKET_HEIGHT / 2.0) * scaling_factor,
        )
        nozzle_bottom_left = (
            self.cx - NOZZLE_WIDTH / 4.0,
            (self.cy + ROCKET_HEIGHT / 2.0 + NOZZLE_HEIGHT) * scaling_factor,
        )
        nozzle_bottom_right = (
            self.cx + NOZZLE_WIDTH / 4.0,
            (self.cy + ROCKET_HEIGHT / 2.0 + NOZZLE_HEIGHT) * scaling_factor,
        )

        # Airbrake points (middle of the rocket body)
        mid_y = self.cy * scaling_factor  # Center of the rocket body
        airbrake_left_base = (self.cx - ROCKET_WIDTH / 2.0, mid_y)
        airbrake_right_base = (self.cx + ROCKET_WIDTH / 2.0, mid_y)
        airbrake_left_tip = (self.cx - ROCKET_WIDTH / 2.0 - AIRBRAKE_LENGTH, mid_y)
        airbrake_right_tip = (self.cx + ROCKET_WIDTH / 2.0 + AIRBRAKE_LENGTH, mid_y)

        # Store all points
        self.original_points = [
            base_left,
            base_right,
            nose_left,
            nose_right,
            nose_tip,
            nozzle_top_left,
            nozzle_top_right,
            nozzle_bottom_left,
            nozzle_bottom_right,
            airbrake_left_base,
            airbrake_left_tip,
            airbrake_right_base,
            airbrake_right_tip,
        ]

    def initialize_widgets(self, context: Context) -> None:
        """
        Initialize widgets with context.
        """
        self.context = context

    @on(Canvas.Resize)
    def resize(self, event: Canvas.Resize) -> None:
        """
        Handle canvas resize.
        """
        self.canvas.reset(size=event.size)
        self.initialize_canvas(event.size.width, event.size.height)
        self.draw_rocket()
        self.pitch_at_last_draw = self.pitch

    def watch_pitch(self) -> None:
        """
        Redraw rocket when pitch change is greater than 2 degrees.
        """
        if abs(self.pitch_at_last_draw - self.pitch) > 2:
            self.draw_rocket()
            self.pitch_at_last_draw = self.pitch

    def watch_state(self) -> None:
        """
        Redraw rocket when state changes.
        """
        self.is_motor_burning = self.state == "MotorBurnState"
        self.draw_rocket()

    def watch_extension(self) -> None:
        """
        Redraw rocket when the airbrakes extension changes.
        """
        self.is_airbrakes_deployed = self.extension in (
            ServoExtension.MAX_NO_BUZZ.value,
            ServoExtension.MAX_EXTENSION.value,
        )
        self.draw_rocket()

    def watch_altitude(self) -> None:
        """
        Redraw altitude axis when altitude changes by more than 2m.
        """
        if abs(self.altitude_at_last_draw - self.altitude) > 1:
            self.draw_rocket()

    def draw_altitude_axis(self) -> None:
        """
        Draw the altitude axis with ticks that scroll based on altitude changes.
        """
        canvas_height = self.canvas.size.height
        middle_y = canvas_height // 2
        current_altitude = self.altitude

        # Define the visible altitude range centered on current_altitude
        alt_range = (canvas_height / 2) * METERS_PER_CELL
        alt_min = current_altitude - alt_range
        alt_max = current_altitude + alt_range

        # Generate tick altitudes within the visible range
        first_tick = np.ceil(alt_min / TICK_INTERVAL) * TICK_INTERVAL
        last_tick = np.floor(alt_max / TICK_INTERVAL) * TICK_INTERVAL
        tick_altitudes = np.arange(first_tick, last_tick + TICK_INTERVAL, TICK_INTERVAL)

        # Map tick altitudes to canvas y-positions
        # Since y increases downward, higher altitudes map to lower y
        tick_ys = [
            round(middle_y - (alt - current_altitude) / METERS_PER_CELL) for alt in tick_altitudes
        ]
        # Filter ticks to ensure they're within canvas bounds
        visible_ticks = [
            (alt, y)
            for alt, y in zip(tick_altitudes, tick_ys, strict=False)
            if 0 <= y < canvas_height
        ]

        # Draw the vertical axis line with integrated ticks
        vertical_quad = (2, 0, 2, 0)  # ┃
        tick_quad = (0, 1, 0, 0)  # ─ (tick to the right)
        tick_positions = {y for _, y in visible_ticks}

        for y in range(canvas_height):
            if y in tick_positions:
                combined_quad = combine_quads(vertical_quad, tick_quad)
                char = get_box(combined_quad)  # e.g., ├
            else:
                char = get_box(vertical_quad)  # ┃
            self.canvas.set_pixel(AXIS_X, y, char, style="#ffffff")

        # Draw labels for visible ticks
        for alt, y in visible_ticks:
            label = f"{alt:.1f}"
            self.canvas.write_text(AXIS_X + 2, y, label)

    def draw_rocket(self) -> None:
        """
        Draw the rocket with the current pitch.
        """
        self.canvas.reset()
        theta = np.radians(self.pitch)
        rotated_points = []

        # Rotate all points around the center
        for x, y in self.original_points:
            dx = x - self.cx
            dy = y - self.cy / ASPECT_RATIO
            x_rot = self.cx + (dx * np.cos(theta) - dy * np.sin(theta))
            y_rot = self.cy + (dx * np.sin(theta) + dy * np.cos(theta)) * ASPECT_RATIO
            rotated_points.append((x_rot, y_rot))

        # Define rocket body lines (existing)
        lines = [
            (
                rotated_points[0][0],
                rotated_points[0][1],
                rotated_points[2][0],
                rotated_points[2][1],
            ),  # Left side
            (
                rotated_points[1][0],
                rotated_points[1][1],
                rotated_points[3][0],
                rotated_points[3][1],
            ),  # Right side
            (
                rotated_points[2][0],
                rotated_points[2][1],
                rotated_points[4][0],
                rotated_points[4][1],
            ),  # Nose left to tip
            (
                rotated_points[3][0],
                rotated_points[3][1],
                rotated_points[4][0],
                rotated_points[4][1],
            ),  # Nose right to tip
            (
                rotated_points[0][0],
                rotated_points[0][1],
                rotated_points[1][0],
                rotated_points[1][1],
            ),  # Base
        ]

        # Add nozzle lines
        lines.extend(
            [
                (
                    rotated_points[0][0],
                    rotated_points[0][1],
                    rotated_points[5][0],
                    rotated_points[5][1],
                ),  # Base left to nozzle top left
                (
                    rotated_points[1][0],
                    rotated_points[1][1],
                    rotated_points[6][0],
                    rotated_points[6][1],
                ),  # Base right to nozzle top right
                (
                    rotated_points[5][0],
                    rotated_points[5][1],
                    rotated_points[7][0],
                    rotated_points[7][1],
                ),  # Nozzle left side
                (
                    rotated_points[6][0],
                    rotated_points[6][1],
                    rotated_points[8][0],
                    rotated_points[8][1],
                ),  # Nozzle right side
                (
                    rotated_points[7][0],
                    rotated_points[7][1],
                    rotated_points[8][0],
                    rotated_points[8][1],
                ),  # Nozzle bottom
            ]
        )

        # Draw airbrakes if deployed
        if self.is_airbrakes_deployed:
            lines.extend(
                [
                    (
                        rotated_points[9][0],
                        rotated_points[9][1],
                        rotated_points[10][0],
                        rotated_points[10][1],
                    ),  # Left airbrake
                    (
                        rotated_points[11][0],
                        rotated_points[11][1],
                        rotated_points[12][0],
                        rotated_points[12][1],
                    ),  # Right airbrake
                ]
            )

        # Draw all lines
        self.canvas.draw_hires_lines(lines, style="#ffffff")

        # Draw the altitude axis:
        self.draw_altitude_axis()
        self.altitude_at_last_draw = self.altitude

        # Draw flames if motor is burning
        if self.is_motor_burning:
            # Calculate nozzle bottom center (new flame origin)
            nozzle_bottom_center_x = (rotated_points[7][0] + rotated_points[8][0]) / 2
            nozzle_bottom_center_y = (rotated_points[7][1] + rotated_points[8][1]) / 2
            nose_tip_x, nose_tip_y = rotated_points[4]
            axis_vector_x = nose_tip_x - nozzle_bottom_center_x
            axis_vector_y = nose_tip_y - nozzle_bottom_center_y
            norm = np.sqrt(axis_vector_x**2 + axis_vector_y**2)

            if norm > 0:  # Avoid division by zero
                unit_vector_x = axis_vector_x / norm
                unit_vector_y = axis_vector_y / norm
                flame_positions = []

                # Extended flame offsets for more "X"s
                for t in FLAME_OFFSETS:
                    flame_x = nozzle_bottom_center_x - t * unit_vector_x
                    flame_y = nozzle_bottom_center_y - t * unit_vector_y
                    flame_positions.append((round(flame_x), round(flame_y)))

                # Optional: Add lateral spread for a wider flame
                perpendicular_vector_x = -unit_vector_y
                perpendicular_vector_y = unit_vector_x
                for t in FLAME_OFFSETS:
                    for offset in [-0.5, 0.5]:  # Small lateral offsets
                        flame_x = (
                            nozzle_bottom_center_x
                            - t * unit_vector_x
                            + offset * perpendicular_vector_x
                        )
                        flame_y = (
                            nozzle_bottom_center_y
                            - t * unit_vector_y
                            + offset * perpendicular_vector_y
                        )
                        flame_positions.append((round(flame_x), round(flame_y)))

                # Draw flames as "X" characters in red
                self.canvas.set_pixels(flame_positions, "X", style="#ff0000")

    def update_visualization(self) -> None:
        """
        Update the visualization with the current context.
        """
        # print("in update_visualization")
        self.pitch = self.context.data_processor.average_pitch
        self.state = self.context.state.name
        self.extension = self.context.servo.current_extension.value
        self.altitude = self.context.data_processor.current_altitude
