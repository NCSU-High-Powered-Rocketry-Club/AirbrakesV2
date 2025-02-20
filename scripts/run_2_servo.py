import time
from adafruit_servokit import ServoKit

# Constants
nbPCAServo = 16
MIN_IMP = [500] * 16
MAX_IMP = [2500] * 16
SERVO_1 = 3
SERVO_2 = 7
SERVO_3 = 10

# Objects
pca = ServoKit(channels=16)

# Function to initialize servos
def init():
    for i in range(nbPCAServo):
        pca.servo[i].set_pulse_width_range(MIN_IMP[i], MAX_IMP[i])
        pca.servo[i].actuation_range = 180

# Function to set servo angles
def set_angle():
    angle = int(input("Enter angle (0-180): "))
    if 0 <= angle <= 180:
        pca.servo[SERVO_1].angle = angle
        pca.servo[SERVO_2].angle = angle
        #pca.servo[SERVO_3].angle = angle
        print(f"Servos set to {angle} degrees")
    else:
        print("Invalid angle. Must be between 0 and 180.")

# Function to oscillate servos
def oscillate():
    angle1 = int(input("Enter first angle (0-180): "))
    angle2 = int(input("Enter second angle (0-180): "))
    delay = float(input("Enter delay between movements (seconds): "))

    if 0 <= angle1 <= 180 and 0 <= angle2 <= 180:
        print("Press Ctrl+C to stop oscillation")
        try:
            pca.servo[SERVO_1].angle = angle1
            pca.servo[SERVO_2].angle = angle1
            time.sleep(0.5)
            while True:
                step = 1 if angle2 > angle1 else -1
                for angle in range(angle1, angle2 + step, step):
                    pca.servo[SERVO_1].angle = angle
                    pca.servo[SERVO_2].angle = angle
                    #pca.servo[SERVO_3].angle = angle
                    time.sleep(delay)
                time.sleep(0.3)
                for angle in range(angle2 - step, angle1 - step, -step):
                    pca.servo[SERVO_1].angle = angle
                    pca.servo[SERVO_2].angle = angle
                    #pca.servo[SERVO_3].angle = angle
                    time.sleep(delay)
                time.sleep(0.2)
        except KeyboardInterrupt:
            print("\nOscillation stopped")
    else:
        print("Invalid input. Ensure angles are between 0-180 and delay > 0.")

# Main function
def main():
    init()
    while True:
        print("\nChoose mode:")
        print("1. Set single angle")
        print("2. Oscillate between two angles")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            set_angle()
        elif choice == '2':
            oscillate()
        elif choice == '3':
            while True:
                pca.servo[SERVO_1].angle = None
                pca.servo[SERVO_2].angle = None
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
