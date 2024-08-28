"""
Run as `python -m Scripts.test_airbrakes`
"""
from Airbrakes.servo import Servo

# this is the pin that the servo's data wire is plugged into
SERVO_PIN = 32

SERVO_CLOSED_DUTY = 6.3
SERVO_OPEN_DUTY = 9.2
servo = Servo(SERVO_PIN, SERVO_OPEN_DUTY, SERVO_CLOSED_DUTY)

print("Type (1) to deploy and (0) to retract the airbrakes.")
while True:
    command = float(input())
    servo.set_extension(command)
