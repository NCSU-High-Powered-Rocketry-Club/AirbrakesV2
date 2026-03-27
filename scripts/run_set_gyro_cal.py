import time

import firm_client

from airbrakes.constants import FIRM_PORT

client = firm_client.FIRMClient(FIRM_PORT)
client.start()


cal = client.get_calibration(timeout_seconds=2.0)

print(f"Before Cal:")
print(f"  accel offsets: {cal.imu_accelerometer_offsets}")
print(f"  accel matrix:  {cal.imu_accelerometer_scale_matrix}")
print(f"  gyro offsets: {cal.imu_gyroscope_offsets}")
print(f"  gyro matrix:  {cal.imu_gyroscope_scale_matrix}")

ACCEL_OFFSETS = cal.imu_accelerometer_offsets
ACCEL_IDENTITY_SCALE = cal.imu_accelerometer_scale_matrix

GYRO_OFFSETS = (0.5254, -0.0618, -0.1175)

GYRO_IDENTITY_SCALE = (
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
)

ok = client.set_imu_calibration(accel_offsets=ACCEL_OFFSETS,
                                accel_scale_matrix=ACCEL_IDENTITY_SCALE,
                                gyro_offsets=GYRO_OFFSETS,
                                gyro_scale_matrix=GYRO_IDENTITY_SCALE,)

time.sleep(.1)

cal = client.get_calibration(timeout_seconds=2.0)

print(f"After Cal:")
print(f"  accel offsets: {cal.imu_accelerometer_offsets}")
print(f"  accel matrix:  {cal.imu_accelerometer_scale_matrix}")
print(f"  gyro offsets: {cal.imu_gyroscope_offsets}")
print(f"  gyro matrix:  {cal.imu_gyroscope_scale_matrix}")

client.stop()
