This folder contains the launch data of actual previous flights. These are used to run the mock replay.

## Data

A description of what happened for each of the launches can be found in the metadata.json file.

## Changes to the raw launch data:

We describe the changes made to each launch data file (if any) in the following list:

1. `purple_launch.csv`:
   
Added fields:
- Quaternions (estOrientQuaternion) 
- Quaternion uncertainities (estAttitudeUncertQuaternion)
- Angular rates (estAngularRate)
- TODO: Add vertical_velocity and vertical_acceleration fields
  
The quaternion uncertainties are set to a low value for a majority of the flight, except whenever 
the altitude is between 500 - 600 meters. During this range, we set the quaternion uncertainties to a high value, to test our code.

2. `shake_n_bake.csv`:

Added fields:
- Renamed `state` to `state_letter`.
- The gravity fields (estGravityVector(X, Y, Z)). Constant gravity was set for estGravityVectorZ.
- Quaternion data (...) 
- invalid_fields
- TODO: Add vertical_velocity and vertical_acceleration fields

There were extra packets added to the file as well, the state_letter for those are "G" (generated) packets. Since we didn't get touchdown data in landed state, we generated a few packets to simulate the touchdown, by only changing the `estCompensatedAccelZ` field. See [#59](https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/59) and [#78](https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/pull/78) for more details.

3. `genesis_launch_1.csv`:

Changes:
- Renamed `state` to `state_letter`.
- LandedState was not detected, so for convenience ~100 mb of useless data has been cropped out of this file.
- `state_letter` was changed to show the actual LandedState (i.e. when we actually hit the ground). The timestamps of the LandedState packets were synced with the timestamps of the last packet in the file. See [#91](https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/issues/91) for more details.

4. `genesis_launch_2.csv`:

Changes to the raw data:
- Renamed `state` to `state_letter`.

5. `legacy_launch_1.csv`: No changes.
6. `legacy_launch_2.csv`: No changes.

7. `pelicanator_launch_1.csv`:

Changes:
- Removed rows where there was no raw and estimated data. This happened because we processed "gpsTimestamp" fields from the IMU (which we don't log),
1000Hz, and our raw frequency was set at 500Hz. So we had rows where there was no useful data.

8. `pelicanator_launch_2.csv`: No changes.
9. `pelicanator_launch_3.csv`: No data recovered.
10. `pelicanator_launch_4.csv`: No changes. TODO: Fuse magnetometer data from payload data?

## Videos

There is a video of the launch from the rocket's perspective in the `videos` folder.

## Metadata

We provide additional context about the launch in the metadata.json file. The date of the launch is
calculated from the timestamp of the first motor burn packet.
