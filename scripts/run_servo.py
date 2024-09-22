"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.run_servo`
For the pi, you will have to use python3
"""

from constants import MAX_EXTENSION, MIN_EXTENSION, SERVO_PIN
from airbrakes.hardware.servo import Servo

servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION)

print("Type (1) to deploy and (0) to retract the airbrakes.")
while True:
    servo.set_extension(float(input()))
