"""
Make sure you are in the root directory of the project, not inside scripts, and run the following
command:

`python -m scripts.run_servo` For the pi, you will have to use python3
"""

from airbrakes.constants import (
    SERVO_MAX_EXTENSION,
    SERVO_MIN_EXTENSION,
)
from airbrakes.hardware.servo import Servo

servo = Servo()

print("0 for testing exending/retracting, 1 for testing positions")
if int(input()) == 0:
    while True:
        print("1 for extending, 0 for retracting")
        if int(input()) == 0:
            servo.retract_airbrakes()
        else:
            servo.extend_airbrakes()
else:
    while True:
        print("0 is min, 1 is max")
        match int(input()):
            case 0:
                servo.set_extension(SERVO_MIN_EXTENSION)
            case 1:
                servo.set_extension(SERVO_MAX_EXTENSION)
            case _:
                print("Invalid input")
                continue
