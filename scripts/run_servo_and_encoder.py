"""
Ensure you are in the root directory of the project and run the following command:
uv run scripts/run_servo_and_encoder.py
"""

from airbrakes.constants import ServoExtension, SERVO_PIN
from airbrakes.hardware.servo import Servo
from gpiozero import RotaryEncoder
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Static
from textual.reactive import reactive
from threading import Event
from airbrakes.constants import ENCODER_PIN_A, ENCODER_PIN_B
# from gpiozero.pins.mock import MockFactory, MockPWMPin
import time


class EncoderPositionLabel(Static):
    """A widget to display the encoder position."""

    position: reactive[float] = reactive(0.0)

    def update_position(self, new_position: float):
        self.position = new_position
        self.update(f"Encoder Position: {self.position}")

class ServoControllerApp(App):
    """A Textual App to control the servo and display encoder position."""

    # CSS_PATH = "servo_controller.css"  # Optional: Define custom styles here

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stop_event = Event()
        # Initialize Servo and Rotary Encoder
        self.servo = Servo(SERVO_PIN)
        self.encoder = RotaryEncoder(ENCODER_PIN_A, ENCODER_PIN_B)

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        yield Container(
            EncoderPositionLabel("Encoder position: 0.0", id="encoder_label"),
            Vertical(
                Static("**Servo Control Modes**"),
                Horizontal(
                    Button("Extend", id="extend_btn", variant="success"),
                    Button("Retract", id="retract_btn", variant="error"),
                ),
                Static("**Precise Positions**"),
                Horizontal(
                    Button("Min", id="min_btn", variant="primary"),
                    Button("Min No Buzz", id="min_no_buzz_btn", variant="primary"),
                    Button("Max", id="max_btn", variant="primary"),
                    Button("Max No Buzz", id="max_no_buzz_btn", variant="primary"),
                ),
                classes="control_section"
            ),
            classes="main_container"
        )
        yield Footer()

    async def on_mount(self):
        """Called when the app is mounted. Start the encoder updater thread."""
        self.encoder_label = self.query_one("#encoder_label", EncoderPositionLabel)
        # Start the encoder updater in a separate thread
        self.run_worker(self.update_encoder_position, thread=True, exclusive=True, name="encoder_thread")

    def update_encoder_position(self):
        """Continuously update the encoder position."""
        while not self.stop_event.is_set():
            current_position = self.encoder.value
            # Schedule the label update on the main thread
            self.encoder_label.update_position(current_position)
            time.sleep(0.1)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Catch button press events and handle them."""
        match event.button.id:
            case "extend_btn":
                self.servo.set_extended()
                # self.encoder.value = 1.0  # Simulate encoder change
            case "retract_btn":
                self.servo.set_retracted()
                # self.encoder.value = 0.0  # Simulate encoder change
            case "min_btn":
                self.servo._set_extension(ServoExtension.MIN_EXTENSION)
                # self.encoder.value = 0.0
            case "min_no_buzz_btn":
                self.servo._set_extension(ServoExtension.MIN_NO_BUZZ)
                # self.encoder.value = 0.1
            case "max_btn":
                self.servo._set_extension(ServoExtension.MAX_EXTENSION)
                # self.encoder.value = 1.0
            case "max_no_buzz_btn":
                self.servo._set_extension(ServoExtension.MAX_NO_BUZZ)
                # self.encoder.value = 0.9
            case _:
                pass  # Handle unknown buttons if necessary

    async def on_unmount(self) -> None:
        """Handle app shutdown."""
        self.stop_event.set()

if __name__ == "__main__":
    app = ServoControllerApp()
    app.run()
