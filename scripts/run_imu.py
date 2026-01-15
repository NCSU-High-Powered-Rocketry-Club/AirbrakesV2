"""
Make sure you are in the root directory of the project, not inside scripts, and run the following
command: `python -m scripts.run_imu` For the pi, you will have to use python3.
"""

from airbrakes.constants import IMU_PORT
from airbrakes.hardware.imu import IMU
from airbrakes.data_handling.packets.imu_data_packet import RawDataPacket
from airbrakes.utils import convert_ns_to_s


imu = IMU(IMU_PORT)
imu.start()

try:
    prev_raw_timestamp = 0.0
    prev_est_timestamp = 0.0
    while True:
        packet = imu.get_imu_data_packet()
        if isinstance(packet, RawDataPacket):
            dt = packet.timestamp - prev_raw_timestamp
            dt_in_seconds = convert_ns_to_s(dt)
            if dt_in_seconds > 0.01:
                print("dt spike", dt_in_seconds)
            prev_raw_timestamp = packet.timestamp
        else:
            dt = packet.timestamp - prev_est_timestamp
            dt_in_seconds = convert_ns_to_s(dt)
            if dt_in_seconds > 0.01:
                print("dt spike", dt_in_seconds)
            prev_est_timestamp = packet.timestamp
except KeyboardInterrupt:  # Stop running IMU if the user presses Ctrl+C
    pass
finally:
    imu.stop()
