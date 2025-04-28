This folder contains the launch data of actual previous flights. These are used to run the mock replay.

## Data

1. `interest_launch.csv`: This is the data from the Interest Launch, on September 28th, 2024. The gravity fields were seperately added on later, as well as missing quaternion data, and the "invalid_fields". The
    "G" state is generated packets. Since we didn't get touchdown data in landed state, we generated a few packets to mimmick the touchdown.
    See #59 and #78 for more details.
2. `purple_launch.csv`: This is the data from the Purple Nurple launch, on 16th December, 2023. The quaternions, quaternion uncertainities, and angular rates fields were seperately
    added on later. We do have touchdown data for this launch, however since our rotation data is not accurate, we cannot get a good velocity estimate, and thus the landed state does not trigger. There is no workaround for this, other than using acceleration data to switch to landed state. The quaternion uncertainties are set to a low value for a majority of the flight, except whenever the altitude is between 500 - 600 meters. During this range, we set the quaternion uncertainties to a high value, to test our code.
3. `genesis_launch_1.csv`: This was our first attempt of a control launch with the Genesis subscale rocket. We tried to have it extend its airbrakes for most of coast and then retract them, but later analysis proved that airbrakes didn't deploy during coast. Additionally, the LandedState was incorrectly detected, so for convenience ~100 mb of useless data has been cropped out of this file.
The timestamps of the LandedState packets were synced with the timestamps of the last packet in the file. See #91 for more details.
4. `genesis_launch_2.csv`: This was our second attempt of a control launch with Genesis. For this one we told the airbrakes to deploy once at around the start of CoastState and did not tell them to retract at all. When we recovered the rocket, the fins were extended, by analysis of launch data shows that the airbrakes didn't deploy in CoastState, and most likely deployed sometime either in FreeFall or once the rocket hit the ground. LandedState was mostly correctly detected. See #91 for more details.
5. `legacy_launch_1.csv`: This was the first flight with an encoder and camera. The encoder clearly indicated that airbrakes deployed during coast, but the camera footage was indicated that they deployed during free fall. This launch told us that there is a massive latency coming directly from
the IMU.
6. `legacy_launch_2.csv`: We changed the IMU packet frequency to 50Hz for estimated packets, and 100Hz for raw packets. Unfortunately, this flight was a dud since our velocity was negative even in StandbyState, which indicated that the IMU had severe issues.
7. `pelicanator_launch_1.csv`: This was the first flight of the Pelicanator rocket. The airbrakes deployed during coast for roughly 4 seconds, and then retracted, successfully lowering our apogee by about 60 meters. However, the recovery system of the rocket failed, causing the rocket to crash land. Our Raspberry Pi 5 switched off, resulting in the loss of about 22 seconds of data. The camera was in the payload, which didn't work, so there's no footage of the airbrakes.
8. `pelicanator_launch_2.csv`: This was the second flight of the Pelicanator rocket. The airbrakes
didn't deploy since we significantly undershot our apogee. Everything was else was perfect though.
9. `pelicanator_launch_3.csv`: Final flight before Hunstville. For this flight, the servo died right before launch, requiring a rewrite of the servo logic to work with only one servo. We had on board footage from the payload for the first time, which showed airbrakes deploying correctly in coast. However they were unable to retract mechanically. The rocket was also dragged through the mud by the wind for a long time after landing, which broke the fins, and also corrupting the SD card, and thus we don't have data for this flight.

## Videos

There is a video of the launch from the rocket's perspective in the `videos` folder.

## Metadata

We provide additional context about the launch in the metadata.json file. The date of the launch is
calculated from the timestamp from the first motor burn packet.