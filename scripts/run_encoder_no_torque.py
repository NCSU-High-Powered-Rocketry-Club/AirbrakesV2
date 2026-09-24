from airbrakes.hardware.servo import Servo
import time

servo = Servo()
servo.start()
try:
    while True:
        servo.set_powered(False)
        print(servo.get_servo_data_packet())
        time.sleep(0.5)
except KeyboardInterrupt:
    servo.stop()