"""
Make sure you are in the root directory of the project, not inside Scripts, and run the following command:
`python -m Scripts.test_servo`
For the pi, you will have to use python3
"""

from Airbrakes.servo import Servo

# The pin that the servo's data wire is plugged into, in this case the GPIO 12 pin which is used for PWM
SERVO_PIN = 12

# The minimum and maximum position of the servo, its range is -1 to 1
MIN_EXTENSION = -1
MAX_EXTENSION = 1

servo = Servo(SERVO_PIN, MIN_EXTENSION, MAX_EXTENSION)

print("Type (1) to deploy and (0) to retract the airbrakes.")
while True:
    servo.set_extension(float(input()))

