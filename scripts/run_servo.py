"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.run_servo`
For the pi, you will have to use python3
"""

from constants import ServoExtension, SERVO_PIN
from airbrakes.hardware.servo import Servo

servo = Servo(SERVO_PIN)

print("0 for testing extending/retracting, 1 for testing positions")
if int(input()) == 0:
    while True:
        print("1 for extending, 0 for retracting")
        if int(input()) == 0:
            servo.set_retracted()
        else:
            servo.set_extended()
else:
    print("0 is min, 1 is max")
    while True:
        match int(input()):
            case 0:
                servo._set_extension(ServoExtension.MIN_EXTENSION)
            case 1:
                servo._set_extension(ServoExtension.MAX_EXTENSION)
            case _:
                print("Invalid input")
                continue
