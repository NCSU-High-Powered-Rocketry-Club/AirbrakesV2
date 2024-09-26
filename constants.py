"""Contains the constants used in the airbrakes module"""

from pathlib import Path

from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket
from airbrakes.utils import get_imu_data_processor_public_properties

# -------------------------------------------------------
# Main
# -------------------------------------------------------

# These are used for simulations
MOCK_ARGUMENT = "mock"
SIMULATION_LOG_NAME = "2023-12-16_17_11_35_mergedLORDlog.csv"  # This should be logged in the logs folder

# -------------------------------------------------------
# Servo Configuration
# -------------------------------------------------------

# The pin that the servo's data wire is plugged into, in this case the GPIO 12 pin which is used for PWM
SERVO_PIN = 12

# The minimum and maximum position of the servo, its range is -1 to 1
MIN_EXTENSION = -0.2 
MIN_NOBUZZ = -.12
MAX_EXTENSION = 0.2605
MAX_NOBUZZ = .2

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

# The headers for the CSV file
CSV_HEADERS = [
    "state",
    "extension",
    *list(IMUDataPacket.__struct_fields__),
    *list(RawDataPacket.__struct_fields__)[1:],  # Skip the first field which is the timestamp
    *list(EstimatedDataPacket.__struct_fields__)[1:],
    # Only add fields that are public properties of the IMUDataProcessor:
    *get_imu_data_processor_public_properties(),
]

# The signal to stop the logging process, this will be put in the queue to stop the process
# see stop() and _logging_loop() for more details.
STOP_SIGNAL = "STOP"

# -------------------------------------------------------
# State Machine Configuration
# -------------------------------------------------------

# Arbitrarily set values for transition between states:

# Standby to MotorBurn:
ACCLERATION_NOISE_THRESHOLD = 0.3  # m/s^2

# We will take the magnitude of acceleration for this
TAKEOFF_HEIGHT = 10  # meters
TAKEOFF_SPEED = 10  # m/s

# MotorBurn to Coasting:
# Acceleration inside this range will be considered as the motor burnout acceleration
ACCELERATION_AT_MOTOR_BURNOUT = [0.0, 6.0]  # m/s^2  (only gravity should be acting on the rocket)
HIGH_SPEED_AT_MOTOR_BURNOUT = 60.0  # m/s
MOTOR_BURN_TIME = 2.3  # seconds

# Coasting to Free fall:

# Basically we don't care about switching from flight to free fall state very quickly, so if the
# current altitude is 250 meters less than our max, then we switch
DISTANCE_FROM_APOGEE = 250  # meters

# Free fall to Landing:

# Consider the rocket to have landed if it is within 15 meters of the launch site height.
GROUND_ALTITIUDE = 15.0  # meters

# -------------------------------------------------------
# Apogee Prediction Configuration
# -------------------------------------------------------

# The altitude at which the rocket is expected to reach apogee, without the airbrakes
TARGET_ALTITUDE = 1554  # m (5,100 ft)
