import time    #https://docs.python.org/fr/3/library/time.html
from adafruit_servokit import ServoKit    #https://circuitpython.readthedocs.io/projects/servokit/en/latest/

#Constants
nbPCAServo=4

#Parameters

MIN_IMP  =[500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500, 500]
MAX_IMP  =[2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500, 2500]
MIN_ANG = 0
MAX_ANG = 270  # limit by the servo

#Objects
pca = ServoKit(channels=16)

# function init 
def init():
    for i in range(nbPCAServo):
        pca.servo[i].set_pulse_width_range(MIN_IMP[i] , MAX_IMP[i])
        pca.servo[i].actuation_range = 270

# function main 
def main():
    init()
    pcaScenario();

# function pcaScenario 
def pcaScenario():
    """Scenario to test servo"""
    for j in range(MIN_ANG,MAX_ANG,1):
        print(f"Send angle {j}")
        # time.sleep(0.01)
        pca.servo[0].angle = j
        pca.servo[3].angle = j
        time.sleep(0.01)

if __name__ == "__main__":
    main()