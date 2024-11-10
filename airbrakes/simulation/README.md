## Rotation Guide for sim IMU

Vertical orientation of the IMU is described in vector form.
- Example: If the -x axis of the IMU is facing the sky, the vertical orientation is [-1, 0, 0]

Direction the rocket leans to on the pad is the launch_pad_direction. Ranges from 0 to 360 degrees.
Important to note that the IMU does not change position inside of the rocket when changing launch pad angle.