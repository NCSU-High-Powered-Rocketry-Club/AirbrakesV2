"""Contains the constants used in the airbrakes module"""

from pathlib import Path

from airbrakes.imu.imu_data_packet import EstimatedDataPacket, IMUDataPacket, RawDataPacket

# -------------------------------------------------------
# Servo Configuration
# -------------------------------------------------------

# The pin that the servo's data wire is plugged into, in this case the GPIO 12 pin which is used for PWM
SERVO_PIN = 12

# The minimum and maximum position of the servo, its range is -1 to 1
MIN_EXTENSION = -1
MAX_EXTENSION = 1

# -------------------------------------------------------
# IMU Configuration
# -------------------------------------------------------

# The port that the IMU is connected to
PORT = "/dev/ttyACM0"

# The frequency in Hz that the IMU will be polled at
FREQUENCY = 100  # TODO: Remove this since we don't/can't control the frequency from the code.

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
    *list(IMUDataPacket.__slots__),
    *list(RawDataPacket.__slots__),
    *list(EstimatedDataPacket.__slots__),
]  # TODO: this needs to be used in the logger module
