"""
Make sure you are in the root directory of the project, not inside scripts, and run the following command:
`python -m scripts.test_imu`
For the pi, you will have to use python3
"""

from constants import FREQUENCY, PORT, UPSIDE_DOWN, TEST_LOGS_PATH
from airbrakes.hardware.imu import IMU
from airbrakes.data_handling.logger import Logger
from pathlib import Path

# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
# from collections import deque
# import numpy as np

# # Initialize a deque for each axis to store the last N acceleration values
# N = 100  # Number of points to display
# x_vals = deque(maxlen=N)
# y_vals = deque(maxlen=N)
# z_vals = deque(maxlen=N)
# time_vals = deque(maxlen=N)

# # Initialize the plot
# fig, ax = plt.subplots()
# ax.set_xlim(0, N)
# ax.set_ylim(-2, 2)  # Assuming accelerations range from -2 to 2 g

# x_line, = ax.plot([], [], label='X-axis')
# y_line, = ax.plot([], [], label='Y-axis')
# z_line, = ax.plot([], [], label='Z-axis')

# ax.legend()

# def init():
#     x_line.set_data([], [])
#     y_line.set_data([], [])
#     z_line.set_data([], [])
#     return x_line, y_line, z_line

# def update(frame):
#     # Simulate reading IMU data in real-time
#     a = imu.get_imu_data_packet()
#     if not isinstance(a, EstimatedDataPacket):
#         return x_line, y_line, z_line

#     # Append new data to the deque
#     time_vals.append(len(time_vals))
#     x_vals.append(a.estCompensatedAccelX)
#     y_vals.append(a.estCompensatedAccelY)
#     z_vals.append(a.estCompensatedAccelZ)

#     # Update the plot data
#     x_line.set_data(time_vals, x_vals)
#     y_line.set_data(time_vals, y_vals)
#     z_line.set_data(time_vals, z_vals)

#     return x_line, y_line, z_line

# ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=50)

# plt.xlabel('Time')
# plt.ylabel('Acceleration (g)')
# plt.title('Real-time Acceleration')
# plt.show()

imu = IMU(PORT, FREQUENCY, UPSIDE_DOWN)
imu.start()

logger = Logger(TEST_LOGS_PATH)
logger.start()

while True:
    print(imu.get_imu_data_packet())
