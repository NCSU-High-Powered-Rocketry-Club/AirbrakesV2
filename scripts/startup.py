import gpiozero

# constants
SERVO_PIN.value = 12
MIN_EXTENSION.value = -0.3
MIN_NOBUZZ = -.12
MAX_EXTENSION.value = 0.3
MAX_NOBUZZ = .22

extension = MIN_NOBUZZ

gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()
servo = gpiozero.Servo(SERVO_PIN.value)
servo.value = extension