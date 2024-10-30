"""Contains the constants used in the airbrakes module"""

from enum import Enum
from pathlib import Path

# -------------------------------------------------------
# Servo Configuration
# -------------------------------------------------------

# The pin that the servo's data wire is plugged into, in this case the GPIO 12 pin which is used for PWM
SERVO_PIN = 12
# This is how long the servo approximately takes to move from one extreme to the other
SERVO_DELAY = 0.3


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
# This is used for the mock imu to limit the queue size to a more realistic value
SIMULATION_MAX_QUEUE_SIZE = 15

# -------------------------------------------------------
# Data Processing Configuration
# -------------------------------------------------------

# Should be checked before launch
Z_DOWN = (1, 1, -1)

# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------

# The path of the folder to hold the log files in
LOGS_PATH = Path("logs")
TEST_LOGS_PATH = Path("test_logs")

# The signal to stop the logging process, this will be put in the queue to stop the process
# see stop() and _logging_loop() for more details.
STOP_SIGNAL = "STOP"


# Don't log more than x packets for StandbyState and LandedState
IDLE_LOG_CAPACITY = 5000  # This is equal to (x/2 + x = 3x/2 = 5000 => x = 3333 = 3.33 secs of data)
# Buffer size if CAPACITY is reached. Once the state changes, this buffer will be logged to make sure we don't lose data
LOG_BUFFER_SIZE = 5000

# -------------------------------------------------------
# State Machine Configuration
# -------------------------------------------------------

# Arbitrarily set values for transition between states:

# Standby to MotorBurn:
ACCELERATION_NOISE_THRESHOLD = 0.35  # m/s^2

# We will take the magnitude of acceleration for this
TAKEOFF_HEIGHT = 10  # meters
TAKEOFF_VELOCITY = 10  # m/s

# MotorBurn to Coasting:

# We will only say that the motor has stopped burning if the
# current velocity <= Max velocity * (1 - MAX_VELOCITY_THRESHOLD)
MAX_VELOCITY_THRESHOLD = 0.03
MOTOR_BURN_TIME = 2.6  # seconds (this is slightly higher than the actual burn time, which is 2.2 seconds)

# Coasting to Free fall:
AIRBRAKES_AFTER_COASTING = 1.5  # seconds  (time to wait while coasting before extending the airbrakes)

# Basically we don't care about switching from flight to free fall state very quickly, so if the
# current altitude is 250 meters less than our max, then we switch
DISTANCE_FROM_APOGEE = 100  # meters

# Free fall to Landing:

# Consider the rocket to have landed if it is within 15 meters of the launch site height.
GROUND_ALTITUDE = 15.0  # meters

# -------------------------------------------------------
# Apogee Prediction Configuration
# -------------------------------------------------------

# This is the standard gravity on Earth, in m/s^2
GRAVITY = 9.798

# The altitude at which the rocket is expected to reach apogee, without the airbrakes
TARGET_ALTITUDE = 1700  # m (5,100 ft)
CURVE_FIT_INITIAL = [-10.5, 0.03]
APOGEE_PREDICTION_FREQUENCY = 100  # packets
