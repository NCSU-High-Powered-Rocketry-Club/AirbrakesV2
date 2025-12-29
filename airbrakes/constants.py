"""
Contains the constants used in the Airbrakes module.
"""

import math
from enum import Enum
from pathlib import Path

# -------------------------------------------------------
# Main Configuration
# -------------------------------------------------------

BUSY_WAIT_SECONDS = 0.1
"""
The amount of time to sleep while busy waiting in a loop.
"""

# -------------------------------------------------------
# Servo Configuration (DS3235 SG)
# -------------------------------------------------------

SERVO_MIN_PULSE_WIDTH_US = 500
"""
The minimum pulse width in microseconds that the servo will accept.

This is the pulse width that corresponds to the minimum rotation of the servo.
"""

SERVO_MAX_PULSE_WIDTH_US = 2500
"""
The maximum pulse width in microseconds that the servo will accept.

This is the pulse width that corresponds to the maximum rotation of the servo.
"""

SERVO_MIN_ANGLE_DEGREES = 0
"""
The minimum angle that the servo can rotate to.
"""

SERVO_MAX_ANGLE_DEGREES = 180
"""
The maximum angle that the servo can rotate to.
"""

SERVO_OPERATING_FREQUENCY_HZ = 50
"""
The operating frequency of the servo in Hertz.

It supports 50-330Hz.
"""

SERVO_CHANNEL = 2
"""
The PWM channel the servo is connected to on the Pi.

Channel 2 corresponds to GPIO Pin 18.
See https://pypi.org/project/rpi-hardware-pwm/ for more information.
"""

SERVO_DELAY_SECONDS = 1.0
"""
This is how long the servo approximately takes to move from one extreme to the other.

This is used for the no buzz code, to make sure the servo has enough time to move to the desired
position.
"""


class ServoExtension(Enum):
    """
    Enum that represents the extension of the servo motor.

    First we set it to an extreme, then to the actual position. This is to ensure that the servo
    will move fast enough and with enough power to actually make it to the position, but then once
    it's there, we don't want it to keep straining past the physical bounds of the air brakes. The
    range of the servo is from 0 to 180 degrees, but we only use a portion of that range to prevent
    the servo from straining too much. We obtained the below values through guess and check, and
    they differ depending on the design.
    """

    # in degrees:
    MIN_EXTENSION = 74
    MIN_NO_BUZZ = 78

    MAX_EXTENSION = 124
    MAX_NO_BUZZ = 121


# -------------------------------------------------------
# Encoder Configuration
# -------------------------------------------------------

ENCODER_RESOLUTION = 20
"""
The points per revolution of the encoder.
"""

ENCODER_PIN_A = 23
"""
The GPIO pin that the encoder's A pin is connected to.
"""

ENCODER_PIN_B = 24
"""
The GPIO pin that the encoder's B pin is connected to.
"""

# -------------------------------------------------------
# Buzzer Configuration
# -------------------------------------------------------

BUZZER_PIN = 7
"""
The GPIO pin the buzzer is connected to.
"""


# -------------------------------------------------------
# Display Configuration
# -------------------------------------------------------

MOCK_DISPLAY_UPDATE_RATE = 1 / 15
"""
The frequency at which the display updates in replay or sim mode.

Increasing this value will negatively affect the performance when running with a "fast" simulation.
"""

REALTIME_DISPLAY_UPDATE_RATE = 1 / 10  # 10 Hz
"""
The frequency at which the display updates in real mode.

Decreasing this value will not show major performance improvements, but increasing it will
negatively affect the performance.
"""


GRAPH_DATA_STORE_INTERVAL_SECONDS = 4
"""
The interval in seconds at which the graph data is stored.

This is used so that it is easy to look at the changing data in real time.
"""

RIGHT_TRIANGLE = "▶"
LEFT_TRIANGLE = "◀"
"""
The icons used to represent the simulation speed.
"""

LIGHT_THEME = "textual-light"
"""
The name of the light theme.
"""

DARK_THEME = "catppuccin-mocha"
"""
The name of the dark theme.
"""


# Constants for rocket dimensions (in canvas cells)
ROCKET_WIDTH = 6
ROCKET_HEIGHT = 15
NOSECONE_HEIGHT = 5
ASPECT_RATIO = 0.5  # Terminal cell width-to-height ratio (roughly)
NOZZLE_HEIGHT = 2  # Height of the nozzle in cells
NOZZLE_WIDTH = ROCKET_WIDTH / 2.0  # Width of the nozzle in cells
FLAME_OFFSETS: list[float] = [0.5, 1, 1.5, 2, 2.5, 3]  # Distances in cells where "X" flames appears
AIRBRAKE_LENGTH = 2  # Length of airbrakes in cells

# Constants for altitude axis
TICK_INTERVAL = 1.7  # meters per tick  (NOT TO SCALE)
AXIS_X = 0  # x-position of the axis
METERS_PER_CELL = 0.15  # Meters per canvas cell (defines scale)

# -------------------------------------------------------
# Data Processor Configuration
# -------------------------------------------------------

WINDOW_SIZE_FOR_PRESSURE_ZEROING = 3000  # 6 seconds at 500 Hz
"""
The number of packets to use for zeroing the pressure altitude at the launch pad.
This is used to prevent atmospheric pressure changes from affecting the zeroed out pressure
altitude.
"""

SECONDS_UNTIL_PRESSURE_STABILIZATION = 0.5
"""
After airbrakes retract, it takes some time for the pressure to stabilize.

DataProcessor will wait this amount of time before switching back to using pressure altitude.
"""

# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------

LOGS_PATH = Path("logs")
"""
The path of the folder to hold the log files in.
"""
TEST_LOGS_PATH = Path("test_logs")
"""
The path of the folder to hold the test log files in.
"""
NUMBER_OF_LINES_TO_LOG_BEFORE_FLUSHING = 1000  # 1 second of data
"""
The number of lines we log before manually flushing the buffer and forcing the OS to write to the
file.
"""

STOP_SIGNAL = "STOP"
"""
The signal to stop the IMU, Logger, and ApogeePredictor thread, this will be put in the queue to
stop the threads.
"""

# Formula for converting number of packets to seconds and vice versa:
# If N = total number of packets, T = total time in seconds:
# f = EstimatedDataPacket.frequency + RawDataPacket.frequency = 500 + 500 = 1000 Hz
# T = N/f => T = N/1000

IDLE_LOG_CAPACITY = 5000  # Using the formula above, this is 5 seconds of data
"""
The maximum number of data packets to log in the StandbyState and LandedState.

This is to prevent log file sizes from growing too large. Some of our 2023-2024 launches were >300
mb.
"""
LOG_BUFFER_SIZE = 5000
"""
Buffer size if CAPACITY is reached.

Once the state changes, this buffer will be logged to make sure we don't lose data.
"""


# -------------------------------------------------------
# IMU Configuration
# -------------------------------------------------------

IMU_PORT = "/dev/ttyACM0"
"""
The port that the IMU is connected to.

This is typically the default port where the IMU connects to the Raspberry Pi. "/dev/ttyACM0"
corresponds to the first USB-serial device recognized by the system in Linux.
"""

RAW_DATA_PACKET_SAMPLING_RATE = 1 / 500
"""
The period at which the IMU sends raw data packets.

This is the reciprocal of the frequency.
"""
EST_DATA_PACKET_SAMPLING_RATE = 1 / 500
"""
The period at which the IMU sends estimated data packets.

This is the reciprocal of the frequency.
"""

IMU_TIMEOUT_SECONDS = 3.0
"""
The maximum amount of time in seconds the IMU thread is allowed to do something (e.g. read a
packet) before it is considered to have timed out.

This is used to prevent the program from deadlocking if the IMU stops sending data. This is also
used as the max timeout to read from the serial port.
"""

REALTIME_PLAYBACK_SPEED: float = 1.0
"""
The speed at which the Mock IMU plays back the data.

1.0 means real-time playback, 2.0 means maximum speed.
"""

# -------------------------------------------------------
# State Machine Configuration
# -------------------------------------------------------

# Arbitrarily set values for transition between states:

# ----------------- Standby to MotorBurn ----------------
ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED = 0.35
"""
We integrate our acceleration to get velocity, but because IMU has some noise, and other things like
wind or being small bumps can cause this to accumulate even while the rocket is stationary, so we
deadband the acceleration to zero to prevent this.
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
MAX_ALTITUDE_THRESHOLD = 0.95
"""
We don't care too much about accurately changing to the freefall state, so we just check if the
rocket is less than 90% of the max altitude it reached.

We do this because it would be catastrophic if we detected freefall too early.
"""

# ----------------- Freefall to Landing -----------------
MAX_FREE_FALL_SECONDS = 300.0
"""
The maximum amount of time in seconds that the rocket can be in freefall before we consider it to
have landed.

This is to prevent the program from running indefinitely if our code never detects the landing of
the rocket. This value accounts for the worst case scenario of the main parachute deploying at
apogee.
"""

GROUND_ALTITUDE_METERS = 10.0
"""
The zeroed-out altitude (final altitude minus initial altitude) in meters that the rocket must be
under before we consider it to have landed.
"""
LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED = 30.0
"""
The acceleration in m/s^2 that the rocket must be above before we consider it to have landed.

Upon landing, the rocket has a large spike in acceleration that is used to detect landing. Lowered
from 50.0 to 30.0 after Huntsville launch data showed softer landings.
"""

# -------------------------------------------------------
# Apogee Prediction Configuration
# -------------------------------------------------------

TARGET_APOGEE_METERS = 518.16  # 518.16 meters is 1700 feet
"""
The target apogee in meters that we want the rocket to reach.

This is used with our bang-bang controller to determine when to extend and retract the air brakes.
"""

ROCKET_DRY_MASS_KG: float = 4.937
"""
The mass of the entire rocket without propellant in kilograms.
"""

ROCKET_CD: float = 0.45
"""
The drag coefficient of the rocket with airbrakes all the way retracted.
"""

# This is the diameter of the rocket in inches converted to meters, turned into radius, then used to
# calculate cross-sectional area.
ROCKET_CROSS_SECTIONAL_AREA_M2: float = math.pi * (4.0 * 0.0254 / 2) ** 2
"""
The cross-sectional area of the rocket in square meters, with airbrakes all the way retracted.
"""

GRAVITY_METERS_PER_SECOND_SQUARED = 9.81
