import gpiozero

# constants
SERVO_PIN = 12
MIN_EXTENSION = -0.3
MIN_NOBUZZ = -.12
MAX_EXTENSION = 0.3
MAX_NOBUZZ = .22

extension = MIN_NOBUZZ

gpiozero.Device.pin_factory = gpiozero.pins.pigpio.PiGPIOFactory()
servo = gpiozero.Servo(SERVO_PIN)
servo.value = extension