"""Contains the constants used in the airbrakes module"""

from enum import Enum
from pathlib import Path

# -------------------------------------------------------
# Main
# -------------------------------------------------------

# These are used for simulations
MOCK_ARGUMENT = "m"
REAL_SERVO_ARGUMENT = "rs"
SIMULATION_LOG_PATH = Path("scripts/imu_data/winter_2023_launch_data.csv")
# SIMULATION_LOG_PATH = Path("logs/2023-11-18_18_21_52_mergedLORDlog.csv")

# -------------------------------------------------------
# Servo Configuration
# -------------------------------------------------------

# The pin that the servo's data wire is plugged into, in this case the GPIO 12 pin which is used for PWM
SERVO_PIN = 12
# This is how long the servo approximately takes to move from one extreme to the other
SERVO_DELAY = .3


class ServoExtension(Enum):
    """
    Enum that represents the extension of the servo motor. First we set it to an extreme, then to the actual position.
    This is to ensure that the servo will move fast enough and with enough power to actually make it to the position,
    but then once it's there, we don't want it to keep straining past the physical bounds of the air brakes.
    """

    MIN_EXTENSION = -0.5
    MAX_EXTENSION = 0.5
    MIN_NO_BUZZ = -0.05
    MAX_NO_BUZZ = 0.278


# -------------------------------------------------------
# IMU Configuration
# IMU Configuration
# -------------------------------------------------------

# The port that the IMU is connected to
PORT = "/dev/ttyACM0"

# The frequency in Hz that the IMU will be polled at
FREQUENCY = 100  # TODO: Remove this since we don't/can't control the frequency from the code.

# The "IDs" of the data packets that the IMU sends
ESTIMATED_DESCRIPTOR_SET = 130
RAW_DESCRIPTOR_SET = 128

# The maximum size of the data queue for the packets, so we don't run into memory issues
MAX_QUEUE_SIZE = 100000

# -------------------------------------------------------
# Orientation Configuration
# -------------------------------------------------------

# Should be checked before launch
UPSIDE_DOWN = False

# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------

# The path of the folder to hold the log files in
LOGS_PATH = Path("logs")
TEST_LOGS_PATH = Path("test_logs")

# The signal to stop the logging process, this will be put in the queue to stop the process
# see stop() and _logging_loop() for more details.
STOP_SIGNAL = "STOP"

DATA_PACKET_DECIMAL_PLACES = 8

# Don't log more than x packets for StandbyState and LandedState
LOG_CAPACITY_AT_STANDBY = 5000
# Buffer size if CAPACITY is reached. Once the state changes, this buffer will be logged to make sure we don't lose data
LOG_BUFFER_SIZE = 5000

# -------------------------------------------------------
# State Machine Configuration
# -------------------------------------------------------

# Arbitrarily set values for transition between states:

# Standby to MotorBurn:
ACCELERATION_NOISE_THRESHOLD = 0.35   # m/s^2

# We will take the magnitude of acceleration for this
TAKEOFF_HEIGHT = 10  # meters
TAKEOFF_SPEED = 10  # m/s

# MotorBurn to Coasting:
# Acceleration inside this range will be considered as the motor burnout acceleration
ACCELERATION_AT_MOTOR_BURNOUT = [0.0, 6.0]  # m/s^2  (only gravity should be acting on the rocket)
HIGH_SPEED_AT_MOTOR_BURNOUT = 60.0  # m/s
MOTOR_BURN_TIME = 2.25  # seconds (this is slightly higher than the actual burn time, which is 2.2 seconds)

# Coasting to Free fall:

# Basically we don't care about switching from flight to free fall state very quickly, so if the
# current altitude is 250 meters less than our max, then we switch
DISTANCE_FROM_APOGEE = 100  # meters

# Free fall to Landing:

# Consider the rocket to have landed if it is within 15 meters of the launch site height.
GROUND_ALTITIUDE = 15.0  # meters

# -------------------------------------------------------
# Apogee Prediction Configuration
# -------------------------------------------------------

# The altitude at which the rocket is expected to reach apogee, without the airbrakes
TARGET_ALTITUDE = 1554  # m (5,100 ft)
