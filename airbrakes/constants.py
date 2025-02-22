"""Contains the constants used in the Airbrakes module."""

from enum import Enum, StrEnum
from pathlib import Path

# -------------------------------------------------------
# Main Configuration
# -------------------------------------------------------

MAIN_PROCESS_PRIORITY = -11
"""The priority of the Main process. This is a really high priority so the OS knows to give it
priority over other processes. This is because we want to make sure we don't want to stay behind
on processing the packets from the IMU. It's a bit lower than the IMU process because we want to
make sure the IMU process is always running and getting data."""


# -------------------------------------------------------
# Servo Configuration
# -------------------------------------------------------

SERVO_PIN = 25
"""
The pin on the pi that the servo's signal wire is plugged into. You can read more about the pins
here: https://www.youngwonks.com/blog/Raspberry-Pi-4-Pinout
"""
SERVO_DELAY_SECONDS = 0.3
"""
This is how long the servo approximately takes to move from one extreme to the other. This is
used for the no buzz code, to make sure the servo has enough time to move to the desired
position.
"""


class ServoExtension(Enum):
    """
    Enum that represents the extension of the servo motor. First we set it to an extreme, then to
    the actual position. This is to ensure that the servo will move fast enough and with enough
    power to actually make it to the position, but then once it's there, we don't want it to keep
    straining past the physical bounds of the air brakes.
    The range of the input for the servo is -1 to 1, where -1 is the minimum rotation and 1 is the
    maximum rotation. We obtained these values through guess and check.
    """

    MIN_EXTENSION = -0.75
    MAX_EXTENSION = 0.055
    MIN_NO_BUZZ = -0.72
    MAX_NO_BUZZ = 0.01


# -------------------------------------------------------
# Encoder Configuration
# -------------------------------------------------------

ENCODER_RESOLUTION = 20
"""The points per revolution of the encoder."""

ENCODER_PIN_A = 23
"""The GPIO pin that the encoder's A pin is connected to."""

ENCODER_PIN_B = 24
"""The GPIO pin that the encoder's B pin is connected to."""


# -------------------------------------------------------
# Display Configuration
# -------------------------------------------------------


class DisplayEndingType(StrEnum):
    """Enum that represents the different ways the display can end."""

    NATURAL = "natural"
    """The display ends naturally, when the rocket lands, in a mock replay."""
    INTERRUPTED = "interrupted"
    """The display ends because the user interrupted the program."""
    TAKEOFF = "takeoff"
    """The display ends because the rocket took off, in a real launch."""


# -------------------------------------------------------
# IMU Configuration
# -------------------------------------------------------

IMU_PORT = "/dev/ttyACM0"
"""
The port that the IMU is connected to. This is typically the default port where the IMU connects
to the Raspberry Pi. "/dev/ttyACM0" corresponds to the first USB-serial device recognized by the
system in Linux.
"""


IMU_PROCESS_PRIORITY = -15
"""The priority of the IMU process. This is a really high priority so the OS knows to give it
priority over other processes. This is because we want to make sure we don't miss any data packets
from the IMU."""

RAW_DATA_PACKET_SAMPLING_RATE = 1 / 1000
"""The period at which the IMU sends raw data packets. This is the reciprocal of the frequency."""
EST_DATA_PACKET_SAMPLING_RATE = 1 / 500
"""
The period at which the IMU sends estimated data packets. This is the reciprocal of the frequency.
"""

ESTIMATED_DESCRIPTOR_SET = 130
"""The ID of the estimated data packet that the IMU sends."""
RAW_DESCRIPTOR_SET = 128
"""The ID of the raw data packet that the IMU sends."""

MAX_FETCHED_PACKETS = 15
"""This is used to limit how many packets we fetch from the packet queue at once."""

MAX_GET_TIMEOUT_SECONDS = 100
"""The maximum amount of time in seconds to wait for a get operation on the queue."""

BUFFER_SIZE_IN_BYTES = 1000 * 1000 * 20  # 20 Mb
"""
The maximum number of bytes to put or get from the queue at once. This is an increase from the
default value of 1Mb, which is too small sometimes for our data packets, e.g. when logging the
entire buffer, which is 5000 packets.
"""

MAX_QUEUE_SIZE = 100_000
"""
The maximum size of the queue that holds the data packets. This is to prevent the queue from"
growing too large and taking up too much memory. This is a very large number, so it should not be
reached in normal operation.
"""

IMU_TIMEOUT_SECONDS = 3.0
"""
The maximum amount of time in seconds the IMU process is allowed to do something (e.g. read a
packet) before it is considered to have timed out. This is used to prevent the program from
deadlocking if the IMU stops sending data.
"""

# Constants for IMU field names and quantifiers
DELTA_THETA_FIELD = 32775
DELTA_VEL_FIELD = 32776
SCALED_ACCEL_FIELD = 32772
SCALED_GYRO_FIELD = 32773
SCALED_AMBIENT_PRESSURE_FIELD = 32791
EST_ANGULAR_RATE_FIELD = 33294
EST_ATTITUDE_UNCERT_FIELD = 33298
EST_COMPENSATED_ACCEL_FIELD = 33308
EST_GRAVITY_VECTOR_FIELD = 33299
EST_LINEAR_ACCEL_FIELD = 33293
EST_ORIENT_QUATERNION_FIELD = 33283
EST_PRESSURE_ALT_FIELD = 33313

X_QUALIFIER = 1
Y_QUALIFIER = 2
Z_QUALIFIER = 3
ATTITUDE_UNCERT_QUALIFIER = 5
PRESSURE_ALT_QUALIFIER = 67
AMBIENT_PRESSURE_QUALIFIER = 58

# -------------------------------------------------------
# Camera Configuration
# -------------------------------------------------------

CAMERA_SAVE_PATH = Path("logs/video.h264")
"""The path that the output of the camera will save to."""

# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------

LOGS_PATH = Path("logs")
"""The path of the folder to hold the log files in."""
TEST_LOGS_PATH = Path("test_logs")
"""The path of the folder to hold the test log files in."""

STOP_SIGNAL = "STOP"
"""
The signal to stop the IMU, Logger, and ApogeePredictor process, this will be put in the queue
to stop the processes.
"""


# Formula for converting number of packets to seconds and vice versa:
# If N = total number of packets, T = total time in seconds:
# f = EstimatedDataPacket.frequency + RawDataPacket.frequency = 500 + 1000 = 1500 Hz
# T = N/f => T = N/1500

IDLE_LOG_CAPACITY = 5000  # Using the formula above, this is 3.33 seconds of data
"""
The maximum number of data packets to log in the StandbyState and LandedState. This is to prevent
log file sizes from growing too large. Some of our 2023-2024 launches were >300 mb.
"""
LOG_BUFFER_SIZE = 5000
"""
Buffer size if CAPACITY is reached. Once the state changes, this buffer will be logged to make
sure we don't lose data.
"""

# -------------------------------------------------------
# State Machine Configuration
# -------------------------------------------------------

# Arbitrarily set values for transition between states:

# ----------------- Standby to MotorBurn ----------------
ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED = 0.35
"""
We integrate our acceleration to get velocity, but because IMU has some noise, and other things
like wind or being small bumps can cause this to accumulate even while the rocket is stationary, so
we deadband the acceleration to zero to prevent this.
"""


TAKEOFF_VELOCITY_METERS_PER_SECOND = 10
"""
The velocity in meters per second that the rocket must reach before we consider it to have taken
off.
"""

# ---------------- MotorBurn to Coasting ----------------
MAX_VELOCITY_THRESHOLD = 0.96
"""
Because the acceleration noise right after the motor burn is very noisy, we will only say that the
motor has stopped burning if the current velocity is less than a percentage of the max velocity.
This helps us predict apogee sooner, because the data used at the beginning of coast phase will be
less noisy.
"""

# ----------------- Coasting to Freefall -----------------
TARGET_ALTITUDE_METERS = 10000
"""
The target altitude in meters that we want the rocket to reach. This is used with our bang-bang
controller to determine when to extend and retract the air brakes.
"""

# ----------------- Freefall to Landing -----------------
MAX_FREE_FALL_SECONDS = 300.0
"""
The maximum amount of time in seconds that the rocket can be in freefall before we consider it to
have landed. This is to prevent the program from running indefinitely if our code never detects the
landing of the rocket. This value accounts for the worst case scenario of the main parachute
deploying at apogee.
"""

GROUND_ALTITUDE_METERS = 10.0
"""
The zeroed-out altitude (final altitude minus initial altitude) in meters that the rocket must be
under before we consider it to have landed.
"""
LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED = 50.0
"""
The acceleration in m/s^2 that the rocket must be above before we consider it to have landed. Upon
landing, the rocket has a large spike in acceleration that is used to detect landing.
"""

# -------------------------------------------------------
# Apogee Prediction Configuration
# -------------------------------------------------------

# This needs to be checked/changed before flights
FLIGHT_LENGTH_SECONDS = 22.0
"""
When we do apogee prediction, we do stepwise integration of our fitted curve to predict the
acceleration, velocity, and altitude curve of the rocket versus time. This is the total time in
seconds that we will integrate over. This is a rough estimate of the time from coast state to
freefall with some extra room for error.
"""

INTEGRATION_TIME_STEP_SECONDS = 1.0 / 500.0
"""This is the delta time that we use for the stepwise integration of our fitted curve. It could
be any value and just corresponds to the precision of our prediction."""

GRAVITY_METERS_PER_SECOND_SQUARED = 9.798
"""This is the standard gravity on Earth for the launch location of the rocket."""

CURVE_FIT_INITIAL = [-10.5, 0.03]
"""The initial guess for the coefficients for curve fit of the acceleration curve."""

APOGEE_PREDICTION_MIN_PACKETS = 10
"""The minimum number of processor data packets required to update the predicted apogee."""

UNCERTAINTY_THRESHOLD = [0.0359, 0.00075]  # For near quick convergence times, use: [0.1, 0.75]
"""
The uncertainty from the curve fit, below which we will say that our apogee has converged. This
uncertainty corresponds to being off by +/- 5m.
"""
