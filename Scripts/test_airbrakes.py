from gpiozero import Servo, Device
from gpiozero.pins.pigpio import PiGPIOFactory

Device.pin_factory = PiGPIOFactory()

servo = Servo(12)

from time import sleep


# try:
#     while True:
#         servo.min()
#         print("min")
#         sleep(0.5)
#         servo.mid()
#         print("mid")
#         sleep(0.5)
#         servo.max()
#         print("max")
#         sleep(0.5)
# except KeyboardInterrupt:
#     print("Program stopped")
#     exit()


while True:
    try:
        print("enter a value -1 to 1")
        servo.value = float(input())
    except KeyboardInterrupt:
        print("Program stopped")
        exit()