"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.run_servo`
For the pi, you will have to use python3
"""

from airbrakes.constants import ServoExtension, SERVO_1_CHANNEL, SERVO_2_CHANNEL , ENCODER_PIN_A, ENCODER_PIN_B
from airbrakes.hardware.servo import Servo

servo = Servo(SERVO_1_CHANNEL, SERVO_2_CHANNEL, ENCODER_PIN_A, ENCODER_PIN_B)

print("0 for testing exending/retracting, 1 for testing positions")
if int(input()) == 0:
    while True:
        print("1 for extending, 0 for retracting")
        if int(input()) == 0:
            servo.set_retracted()
        else:
            servo.set_extended()
else:
    print("0 is min, 1 is min no buzz, 2 is max, 3 is max no buzz")
    while True:
        match int(input()):
            case 0:
                servo._set_extension(ServoExtension.MIN_EXTENSION)
            case 1:
                servo._set_extension(ServoExtension.MIN_NO_BUZZ)
            case 2:
                servo._set_extension(ServoExtension.MAX_EXTENSION)
            case 3:
                servo._set_extension(ServoExtension.MAX_NO_BUZZ)
            case _:
                print("Invalid input")
                continue
