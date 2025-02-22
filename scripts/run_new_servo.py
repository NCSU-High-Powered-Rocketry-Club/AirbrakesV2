from gpiozero import PWMOutputDevice
from time import sleep
from rpi_hardware_pwm import HardwarePWM

SERVO_PIN = 18  # Change this to your GPIO pin
pwm = PWMOutputDevice(SERVO_PIN, frequency=50)  # 50Hz for servo

def set_servo_angle(angle):
    """Convert angle (0-180) to duty cycle (2.5% - 12.5%)."""
    duty_cycle = (angle / 180) * (10) + 2.5  # Scale 0-180° to 2.5%-12.5%
    pwm.value = duty_cycle / 100  # Convert to 0-1 range
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
    pwm.off()
    pwm.close()


