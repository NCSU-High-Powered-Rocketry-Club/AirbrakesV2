import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

imu_data = pd.read_csv(Path('scripts/imu_data/InterestLaunch-9-28 (No Airbrakes Deployed).csv'))
# Filtering relevant columns for computation
fields = ['timestamp', "speed", 'current_altitude', "estLinearAccelX", "estLinearAccelY", "estLinearAccelZ",]
imu_data_filtered = imu_data[fields].dropna()

# Convert timestamps from nanoseconds to seconds
# Zeroing the time axis by subtracting the initial timestamp
imu_data_filtered['timestamp_sec'] = imu_data_filtered['timestamp'] * 1e-9
imu_data_filtered['timestamp_sec'] = imu_data_filtered['timestamp_sec'] - imu_data_filtered['timestamp_sec'].iloc[0]
print(max(imu_data_filtered["timestamp_sec"]))

# error case: in one of our runs, the timestamp produced by the IMU was greater than 5 seconds, 
# sometimes going up to 1750 seconds.
# for i, value in imu_data_filtered["timestamp_sec"].items():
#     if value > 5:
#         print(f"THIS IMU DATA FIELD IS NOT VALID: index: {i}, {value} seconds)")
#         # print the full row
#         print(imu_data_filtered.loc[i])
#         break


# Compute velocity by differentiating estPressureAlt with respect to time
time_diff = np.diff(imu_data_filtered['timestamp_sec'])
position_diff = np.diff(imu_data_filtered['current_altitude'])

# Velocity from pressure altitude differentiation
velocity_from_alt = position_diff / time_diff

# Get acceleration magnitude
# acceleration_magnitude = np.sqrt(imu_data_filtered['estLinearAccelX']**2 + imu_data_filtered['estLinearAccelY']**2 + imu_data_filtered['estLinearAccelZ']**2)
# print(acceleration_magnitude)


# Get velocity vector by integrating each component of acceleration
velocity_x = np.cumsum(imu_data_filtered['estLinearAccelX'][:-1] * time_diff)
velocity_y = np.cumsum(imu_data_filtered['estLinearAccelY'][:-1] * time_diff)
velocity_z = np.cumsum(imu_data_filtered['estLinearAccelZ'][:-1] * time_diff)
velocity_from_accel_component = np.sqrt(velocity_x**2 + velocity_y**2 + velocity_z**2)
print(velocity_from_accel_component)


# Plotting the results
plt.figure(figsize=(12, 6))
# plt.subplot(3, 1, 1)
# plt.plot(imu_data_filtered["time"], acceleration_magnitude, label='Acceleration Magnitude')
# plt.title('Acceleration Magnitude')
# plt.xlabel('Time (seconds)')
# plt.ylabel('Linear accel Mag (m/s^2)')
# plt.grid(True)

# Plot velocity from estPressureAlt differentiation
plt.subplot(3, 1, 1)
plt.plot(imu_data_filtered['timestamp_sec'][:-1], velocity_from_alt, label='Velocity from estPressureAlt')
plt.xlabel('Time (seconds)')
plt.ylabel('Velocity (m/s)')
plt.title('Velocity from estPressureAlt (Differentiation)')
plt.xlim(left=1800)
plt.grid(True)

# # Plot velocity from acceleration integration
plt.subplot(3, 1, 2)
plt.plot(imu_data_filtered['timestamp_sec'][:-1], velocity_from_accel_component, label='Speed from estLinearAccel', color='r')
plt.xlabel('Time (seconds)')
plt.ylabel('Velocity (m/s)')
plt.title('Speed from Linear Accel')
# plt.xlim(left=1800)
plt.grid(True)

# plot altitude
plt.subplot(3, 1, 3)
plt.plot(imu_data_filtered['timestamp_sec'], imu_data_filtered['current_altitude'], label='Estimated Altitude')
plt.xlabel('Time (seconds)')
plt.ylabel('Altitude (m)')
plt.title('Pressure Altitude')
plt.xlim(left=1800)
plt.grid(True)


plt.tight_layout()
plt.savefig("scripts/plots/interest_launch_data.png")
