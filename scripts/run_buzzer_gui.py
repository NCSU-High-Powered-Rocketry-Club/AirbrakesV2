"""
Ensure you are in the root directory of the project and run the following command:
uv run scripts/run_buzzer_gui.py
"""

import gpiozero
from gpiozero import Buzzer, TonalBuzzer
from gpiozero.tones import Tone
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Header, Footer, Static
from textual.reactive import reactive
from time import sleep
# from gpiozero.pins.mock import MockFactory, MockPWMPin


gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()

MARY_HAD_A_LITTLE_LAMB_MELODY = [
    ("E4", 0.4), ("D4", 0.4), ("C4", 0.4), ("D4", 0.4),
    ("E4", 0.4), ("E4", 0.4), ("E4", 0.8), ("D4", 0.4),
    ("D4", 0.4), ("D4", 0.8), ("E4", 0.4), ("G4", 0.4),
    ("G4", 0.8), ("E4", 0.4), ("D4", 0.4), ("C4", 0.4),
    ("D4", 0.4), ("E4", 0.4), ("E4", 0.4), ("E4", 0.4),
    ("E4", 0.4), ("D4", 0.4), ("D4", 0.4), ("E4", 0.4),
    ("D4", 0.4), ("C4", 0.8)
]


class BuzzerValueLabel(Static):
    """A widget to display the encoder position."""

    value: reactive[float] = reactive(0.0)

    def update_position(self, new_position: float):
        self.value = new_position
        self.update(f"Buzzer value: {str(self.value)}")

class BuzzerControllerApp(App):
    """A Textual App to control the servo and display encoder position."""

    # CSS_PATH = "buzzer_control.css"  # Optional: Define custom styles here

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bz = Buzzer(8)
        # self.tonal_bz = TonalBuzzer(8)

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        yield Container(
            BuzzerValueLabel("Buzzer value: 0.0", id="buzzer_label"),
            Vertical(
                Static("**Buzzer Control Modes**"),
                Horizontal(
                    Button("On", id="on_buzzer_btn", variant="success"),
                    Button("Off", id="off_buzzer_btn", variant="error"),
                ),
                Static("**Tonal Buzzer Control Modes**"),
                Horizontal(
                    Button("Play mary had a little lamb", id="on_tonal_buzzer_btn", variant="success"),
                    # Button("Off", id="off_tonal_buzzer_btn", variant="error"),
                ),
                classes="control_section"
            ),
            classes="main_container"
        )
        yield Footer()

    async def on_mount(self):
        """Called when the app is mounted. Start the encoder updater thread."""
        self.buzzer_label = self.query_one("#buzzer_label", BuzzerValueLabel)

    def play_note(self, note, duration):
        """Play a single note for a given duration."""
        if note == "REST":
            return 
        else:
            self.tonal_bz.play(Tone(note))
            sleep(duration)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Catch button press events and handle them."""
        match event.button.id:
            case "on_buzzer_btn":
                self.bz.on()
                self.buzzer_label.update(str(self.bz.value))
                # self.encoder.value = 1.0  # Simulate encoder change
            case "off_buzzer_btn":
                self.bz.off()
                self.buzzer_label.update(str(self.bz.value))
                # self.encoder.value = 0.0  # Simulate encoder change
            case "on_tonal_buzzer_btn":
                for note, duration in MARY_HAD_A_LITTLE_LAMB_MELODY:
                    self.play_note(note, duration)
                    sleep(0.1)  # Short pause between notes
            case _:
                pass  # Handle unknown buttons if necessary

if __name__ == "__main__":
    app = BuzzerControllerApp()
    app.run()
