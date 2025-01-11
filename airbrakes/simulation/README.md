# Rotation Guide for sim IMU

### Axes and Direction Definitions:
#### Vehicle Frame:
- The coordinate system with respect to the IMU inside of the rocket.
#### Earth Frame:
- The coordinate system with respect to Earth frame of reference.
#### WGS Vertical:
- The upwards orientation of the rocket, direction opposite of gravitational force
#### Rocket Body Axis:
- The direction that the rocket is facing; roll axis, longitudinal axis of the rocket
#### Flight Path:
- Velocity vector direction of the rocket; which way the rocket is travelling
#### Azimuth:
- $\phi$, phi, the horizontal cardinal direction of the flight path, relative to Earth's surface
- An azimuth of zero degrees is facing North.

### Angle Vector Definitions:
#### Pitch Angle:
- $\theta$, theta, angle from WGS vertical to the rocket body axis
#### Flight Path Angle:
- $\gamma$, gamma, angle from WGS vertical to the flight path
#### Angle of Attack:
- $\alpha$, alpha, angle from the flight path to the rocket body axis


WGS vertical of the IMU is described in vector form.
- Example: If the -x axis of the IMU is facing the sky, the WGS vertical is [-1, 0, 0]

Important to note that the IMU does not change orientation inside of the rocket when changing launch pad angle.