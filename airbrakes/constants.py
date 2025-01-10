"""Contains the constants used in the airbrakes module"""

from enum import Enum, StrEnum
from pathlib import Path

# -------------------------------------------------------
# Servo Configuration
# -------------------------------------------------------

SERVO_PIN = 25
"""The pin on the pi that the servo's signal wire is plugged into, in this case the GPIO 25 pin. You
can read more about the pins here: https://www.youngwonks.com/blog/Raspberry-Pi-4-Pinout"""
SERVO_DELAY_SECONDS = 0.3
"""This is how long the servo approximately takes to move from one extreme to the other. This is
used for the no buzz code, to make sure the servo has enough time to move to the desired position"""


class ServoExtension(Enum):
    """
    Enum that represents the extension of the servo motor. First we set it to an extreme, then to
    the actual position. This is to ensure that the servo will move fast enough and with enough
    power to actually make it to the position, but then once it's there, we don't want it to keep
    straining past the physical bounds of the air brakes.

    The range of the input for the servo is -1 to 1, where -1 is the minimum rotation and 1 is the
    maximum rotation. We obtained these values through guess and check.
    """

    MIN_EXTENSION = -0.4
    MAX_EXTENSION = 0.7
    MIN_NO_BUZZ = -0.23
    MAX_NO_BUZZ = 0.58


# -------------------------------------------------------
# Display Configuration
# -------------------------------------------------------


class DisplayEndingType(StrEnum):
    """
    Enum that represents the different ways the display can end.
    """

    NATURAL = "natural"
    """The display ends naturally, when the rocket lands, in a mock replay."""
    INTERRUPTED = "interrupted"
    """The display ends because the user interrupted the program."""
    TAKEOFF = "takeoff"
    """The display ends because the rocket took off."""


# -------------------------------------------------------
# Display Configuration
# -------------------------------------------------------

MOCK_DISPLAY_UPDATE_FREQUENCY = 1 / 20  # 20 Hz

REAL_TIME_DISPLAY_UPDATE_FREQUENCY = 1 / 10  # 10 Hz

# -------------------------------------------------------
# IMU Configuration
# -------------------------------------------------------

IMU_PORT = "/dev/ttyACM0"
"""The port that the IMU is connected to. This is typically the default port where the IMU connects
to the Raspberry Pi. "/dev/ttyACM0" corresponds to the first USB-serial device recognized by the
system."""

# The frequency at which the IMU sends data packets, in seconds
RAW_DATA_PACKET_SAMPLING_RATE = 1 / 1000
"""The frequency at which the IMU sends raw data packets, this is 1kHz"""
EST_DATA_PACKET_SAMPLING_RATE = 1 / 500
"""The frequency at which the IMU sends estimated data packets, this is 500Hz"""

# The "IDs" of the data packets that the IMU sends.
ESTIMATED_DESCRIPTOR_SET = 130
"""The ID of the estimated data packet that the IMU sends"""
RAW_DESCRIPTOR_SET = 128
"""The ID of the raw data packet that the IMU sends"""

# This is used by all queues to keep things consistent:
MAX_FETCHED_PACKETS = 15
"""This is used to limit how many packets we fetch from the imu at once."""

# Timeouts for get() queue operations:
MAX_GET_TIMEOUT_SECONDS = 100  # seconds
"""The maximum amount of time in seconds to wait for a get operation on the queue."""

# Max bytes to put/get from the queue at once:
BUFFER_SIZE_IN_BYTES = 1000 * 1000 * 20  # 20 Mb
"""The maximum number of bytes to put or get from the queue at once. This is an increase from the
default value of 1Mb, which is too small sometimes for our data packets, e.g. when logging the
entire buffer, which is 5000 packets."""

MAX_QUEUE_SIZE = 100_000
"""The maximum size of the queue that holds the data packets. This is to prevent the queue from"
growing too large and taking up too much memory. This is a very large number, so it should not be
reached in normal operation."""

IMU_TIMEOUT_SECONDS = 3.0
"""The maximum amount of time in seconds the IMU process to do something (e.g. read a packet) before
it is considered to have timed out. This is used to prevent the program from deadlocking if the IMU
stops sending data."""

# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------

LOGS_PATH = Path("logs")
"""The path of the folder to hold the log files in"""
TEST_LOGS_PATH = Path("test_logs")
"""The path of the folder to hold the test log files in"""

STOP_SIGNAL = "STOP"
"""The signal to stop the logging and the apogee prediction process, this will be put in the queue
to stop the process"""


# Formula for converting number of packets to seconds and vice versa:
# If N = total number of packets, T = total time in seconds:
# f = EstimatedDataPacket.frequency + RawDataPacket.frequency = 500 + 1000 = 1500 Hz
# T = N/f => T = N/1500

IDLE_LOG_CAPACITY = 5000  # Using the formula above, this is 3.33 seconds of data
"""The maximum number of data packets to log in the StandbyState and LandedState. This is to prevent
log file sizes from growing too large. Some of our 2023-2024 launches were >300 mb."""
LOG_BUFFER_SIZE = 5000
"""Buffer size if CAPACITY is reached. Once the state changes, this buffer will be logged to make
sure we don't lose data"""

# -------------------------------------------------------
# State Machine Configuration
# -------------------------------------------------------

# Arbitrarily set values for transition between states:

# ----------------- Standby to MotorBurn ----------------
ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED = 0.35
"""We integrate our acceleration to get velocity, but because IMU has some noise, and other things
like wind or being small bumps can cause this to accumulate even while the rocket is stationary, so
we deadband the accel to prevent this."""

TAKEOFF_HEIGHT_METERS = 10
"""The height in meters that the rocket must reach before we consider it to have taken off."""
TAKEOFF_VELOCITY_METERS_PER_SECOND = 10
"""The velocity in meters per second that the rocket must reach before we consider it to have taken
off."""

# ---------------- MotorBurn to Coasting ----------------
MAX_VELOCITY_THRESHOLD = 0.96
"""Because motors can behave unpredictably near the end of their burn, we will only say that the
motor has stopped burning if the current velocity is less than a percentage of the max velocity."""

# ----------------- Coasting to Freefall -----------------
TARGET_ALTITUDE_METERS = 1000
"""The target altitude in meters that we want the rocket to reach. This is used with our bang-bang
controller to determine when to extend and retract the airbrakes."""

# ----------------- Freefall to Landing -----------------
MAX_FREE_FALL_SECONDS = 300.0
"""The maximum amount of time in seconds that the rocket can be in freefall before we consider it to
have landed. This is to prevent the program from running indefinitely if our code never detects the
landing of the rocket. This value accounts for the worst case scenario of the main parachute
deploying at apogee."""

GROUND_ALTITUDE_METERS = 10.0
"""The altitude in meters that the rocket must be under before we consider it to have landed."""
LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED = 50.0
"""The acceleration in m/s^2 that the rocket must be above before we consider it to have landed."""

# -------------------------------------------------------
# Apogee Prediction Configuration
# -------------------------------------------------------

# This needs to be checked/changed before flights
FLIGHT_LENGTH_SECONDS = 22.0
"""When we do apogee prediction, we do stepwise integration of our fitted curve to predict the
accel, velocity, and altitude curve of the rocket. This is the total time in seconds that we will
predict for. This is a rough estimate of the time from coast state to freefall with some extra room
for error."""

INTEGRATION_TIME_STEP_SECONDS = 1.0 / 500.0
"""This is the dt that we use for the stepwise integration of our fitted curve. It could be any
value and just corresponds to the precision of our prediction."""

GRAVITY_METERS_PER_SECOND_SQUARED = 9.798
"""This is the standard gravity on Earth."""

CURVE_FIT_INITIAL = [-10.5, 0.03]
"""The initial guess for the coefficients for curve fit of the acceleration curve."""

APOGEE_PREDICTION_MIN_PACKETS = 10
"""The minimum number of data packets required to predict the apogee."""

UNCERTAINTY_THRESHOLD = [0.0359, 0.00075]  # For near quick convergence times, use: [0.1, 0.75]
"""The uncertainty from the curve fit, below which we will say that our apogee has converged. This
uncertainty corresponds to being off by +/- 5m."""
