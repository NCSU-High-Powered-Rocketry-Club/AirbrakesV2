from rpi_hardware_pwm import HardwarePWM
from time import sleep

pwm = HardwarePWM(pwm_channel=2, hz=50, chip=0)
pwm.start(100)

def set_servo_angle(angle):
    """Convert angle (0-180) to duty cycle (2.5% - 12.5%)."""
    duty_cycle = (angle / 180) * (10) + 2.5  # Scale 0-180° to 2.5%-12.5%
    pwm.change_duty_cycle(duty_cycle / 100)
    sleep(0.3)  # Allow servo to reach position

try:
    while True:
        angle = float(input("Enter angle (0-180): "))
        if 0 <= angle <= 180:
            set_servo_angle(angle)
        else:
            print("Invalid angle. Enter 0-180.")
except KeyboardInterrupt:
    print("\nExiting...")
finally:
    pwm.stop()