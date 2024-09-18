"""Contains the constants used in the airbrakes module"""

from pathlib import Path

from airbrakes.imu.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket

# -------------------------------------------------------
# Servo Configuration
# -------------------------------------------------------

# The pin that the servo's data wire is plugged into, in this case the GPIO 12 pin which is used for PWM
SERVO_PIN = 12

# The minimum and maximum position of the servo, its range is -1 to 1
MIN_EXTENSION = -0.0999  # -.079
MAX_EXTENSION = 0.2605

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
UPSIDE_DOWN = True  # TODO: Currently not factored in the implementation should be added to DataProcessor

# -------------------------------------------------------
# Logging Configuration
# -------------------------------------------------------

# The path of the folder to hold the log files in
LOGS_PATH = Path("logs")

# The headers for the CSV file
CSV_HEADERS = [
    "state",
    "extension",
    *list(IMUDataPacket.__struct_fields__),
    *list(RawDataPacket.__struct_fields__)[1:],  # Skip the first field which is the timestamp
    *list(EstimatedDataPacket.__struct_fields__)[1:],
]

# The signal to stop the logging process, this will be put in the queue to stop the process
# see stop() and _logging_loop() for more details.
STOP_SIGNAL = "STOP"
