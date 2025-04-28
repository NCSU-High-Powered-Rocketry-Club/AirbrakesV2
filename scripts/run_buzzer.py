"""
Ensure you are in the root directory of the project and run the following command:
uv run scripts/run_buzzer.py. This is run when the Pi connects to the hotspot.
"""


import gpiozero
from gpiozero import Buzzer
import time
from airbrakes.constants import BUZZER_PIN

from gpiozero.pins.lgpio import LGPIOFactory

gpiozero.Device.pin_factory = LGPIOFactory()


def switch_on(bz: Buzzer):
    bz.on()

def switch_off(bz: Buzzer):
    bz.off()


if __name__ == "__main__":
    bz = Buzzer(BUZZER_PIN)

    switch_on(bz)
    time.sleep(1)
    switch_off(bz)
