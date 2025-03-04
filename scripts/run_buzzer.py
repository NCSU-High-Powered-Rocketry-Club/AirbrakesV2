"""
Ensure you are in the root directory of the project and run the following command:
uv run scripts/run_buzzer.py. This is run when the Pi connects to the hotspot.
"""


import gpiozero
from gpiozero import Buzzer
import time


gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()


def switch_on(bz: Buzzer):
    bz.on()

def switch_off(bz: Buzzer):
    bz.off()


if __name__ == "__main__":
    bz = Buzzer(8)

    switch_on(bz)
    time.sleep(1)
    switch_off(bz)
