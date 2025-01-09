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


## Metadata

We provide additional context about the launch in the metadata.json file.