"""
Ensure you are in the root directory of the project and run the following command:
uv run scripts/run_servo_and_encoder.py
"""

from airbrakes.constants import SERVO_1_CHANNEL, SERVO_2_CHANNEL, SERVO_MAX_ANGLE, ServoExtension
from airbrakes.hardware.servo import Servo
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Static, Input
from textual.reactive import reactive
from threading import Event
from airbrakes.constants import ENCODER_PIN_A, ENCODER_PIN_B
# from gpiozero.pins.mock import MockFactory, MockPWMPin
import time

class EncoderPositionLabel(Static):
    """
    A widget to display the encoder position.
    """

    position: reactive[float] = reactive(0.0)

    def update_position(self, new_position: float):
        self.position = new_position
        self.update(f"Encoder Position: {self.position}")

class ServoControllerApp(App):
    """
    A Textual App to control the servo and display encoder position.
    """

    # CSS_PATH = "servo_controller.css"  # Optional: Define custom styles here

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stop_event = Event()
        # Initialize Servo and Rotary Encoder
        self.servo = Servo(SERVO_1_CHANNEL, SERVO_2_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)
        self.encoder = self.servo.encoder

    def compose(self) -> ComposeResult:
        """
        Compose the UI layout.
        """
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
                # Added Servo Value Input Section
                Static("**Set Servo Value (-1 to 1)**"),
                Horizontal(
                    Input(placeholder="Enter value between -1 and 1", id="servo_input"),
                ),
                Button("Set Value", id="set_value_btn", variant="primary"),
                classes="control_section"
            ),
            classes="main_container"
        )
        yield Footer()

    async def on_mount(self):
        """
        Called when the app is mounted.

        Start the encoder updater thread.
        """
        self.encoder_label = self.query_one("#encoder_label", EncoderPositionLabel)
        self.encoder.when_rotated = self.update_label
        # Reference to the input widget
        self.servo_input = self.query_one("#servo_input", Input)
        # Optionally, add a status message
        self.status = Static("", id="status")
        self.query_one(".control_section").mount(self.status)

    def update_label(self):
        """
        Calls the update_position function to update the encoder label.
        """
        # self.encoder.steps counts the number of steps it has turned, divide by the encoder resolution
        # so that a full revolution of the encoder is either 1.0 or -1.0
        self.encoder_label.update_position(self.encoder.steps)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Catch button press events and handle them.
        """
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
            case "set_value_btn":
                self.handle_set_value()
            case _:
                pass  # Handle unknown buttons if necessary

    def handle_set_value(self):
        """
        Handle setting the servo value from input.
        """
        input_value = self.servo_input.value.strip()
        try:
            value = float(input_value)
            if not 0 <= value <= SERVO_MAX_ANGLE:
                raise ValueError("Value out of range")
            # Assuming the servo's set_position method accepts values from -1 to 1
            self.servo.first_servo.angle = value
            self.servo.second_servo.angle = value
            self.status.update(f"Servo set to {value}")
        except ValueError:
            self.status.update("Invalid input! Enter a number between -1 and 1.")

    async def on_unmount(self) -> None:
        """
        Handle app shutdown.
        """
        self.stop_event.set()

if __name__ == "__main__":
    app = ServoControllerApp()
    app.run()
