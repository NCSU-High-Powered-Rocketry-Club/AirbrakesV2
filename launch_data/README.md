This folder contains the launch data of actual previous flights. These are used to run the mock sim.

## Data

1. `interest_launch.csv`: This is the data from the Interest Launch, on September 28th, 2024. The gravity fields were seperately added on later. The
    "G" state is generated packets. Since we didn't get touchdown data in landed state, we generated a few packets to simulate the touchdown.
    See #59 and #78 for more details.
2. `purple_launch.csv`: This is the data from the Purple Nurple launch, on 16th December, 2023. The quaternions, and angular rates fields were seperately
    added on later. We do have touchdown data for this launch, however since our rotation data is not accurate, we cannot get a good velocity estimate, and thus the landed state does not trigger. There is no workaround for this, other than using acceleration data to switch to landed state.