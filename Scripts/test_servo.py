"""
Make sure you are in the root directory of the project, not inside Scripts, and run the following command:
`python -m Scripts.test_servo`
For the pi, you will have to use python3
"""
from Airbrakes.servo import Servo

servo = Servo()

print("Type (1) to deploy and (0) to retract the airbrakes.")
while True:
    servo.set_extension(float(input()))
