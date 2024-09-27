"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.run_servo`
For the pi, you will have to use python3
"""

from constants import MAX_EXTENSION, MIN_EXTENSION, MIN_NOBUZZ, MAX_NOBUZZ, SERVO_PIN
from airbrakes.hardware.servo import Servo

servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION, MIN_NOBUZZ, MAX_NOBUZZ)

print("Type (1) to deploy and (0) to retract the airbrakes. 2 is max nobuzz, 3 is min nobuzz and 4 is max nobuzz.")
while True:
    servo.set_extension(float(input()))
