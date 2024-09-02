"""
Make sure you are in the root directory of the project, not inside Scripts, and run the following command:
`python -m Scripts.test_servo`
For the pi, you will have to use python3
"""
from Airbrakes.servo import Servo

# The pin that the servo's data wire is plugged into, 32 is for the GPIO 12 pin which is used for PWM
SERVO_PIN = 32

# The duty cycle for the servo to be fully closed and fully open
CLOSED_DUTY_CYCLE = 6.3
OPEN_DUTY_CYCLE = 9.2

servo = Servo(SERVO_PIN, CLOSED_DUTY_CYCLE, OPEN_DUTY_CYCLE)

print("Type (1) to deploy and (0) to retract the airbrakes.")
while True:
    servo.set_extension(float(input()))
