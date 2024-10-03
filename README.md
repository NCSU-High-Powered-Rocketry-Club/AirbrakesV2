# AirbrakesV2 🚀


## Overview
This project is for controlling our Air brakes system with the goal of making our rocket "hit" its target apogee. The code follows the [finite state machine](https://www.tutorialspoint.com/design_pattern/state_pattern.htm) design pattern, using the [`AirbrakesContext`](https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2/blob/main/airbrakes/airbrakes.py) to manage interactions between the states, hardware, logging, and data processing. 


<img alt="graph" src="https://github.com/user-attachments/assets/39cf0556-d388-458b-8668-64177506c9de" width="70%">

This is our interest launch flight data, altitude over time. The different colors of the line are different states the rocket goes through:
1. Stand By - when the rocket is on the rail on the ground
2. Motor Burn - when the motor is burning and the rocket is accelerating
3. Coast - when the motor has burned out and the rocket is coasting, this is when air brakes will be deployed
4. Free Fall - when the rocket is falling back to the ground after apogee, this is when the air brakes will be
retracted
5. Landed - when the rocket has landed on the ground

## Setup

#### Install uv:

[uv](https://docs.astral.sh/uv/getting-started/installation/) is a Python and project manager, which makes handling different Python versions and virtual environments easier.

`curl -LsSf https://astral.sh/uv/install.sh | sh`

This project uses Python 3.12. Using an older version may not work since we use newer language features:

`uv python install 3.12`

#### Clone the repository:

```
git clone https://github.com/yourusername/AirbrakesV2.git
cd AirbrakesV2
```

#### Set up a virtual environment:

```
uv venv
source .venv/bin/activate
```

#### Install the required dependencies:

```uv pip install .[dev]```
_There are libraries that only fully work when running on the Pi (gpiozero, mscl), so if you're having trouble importing them locally, program the best you can and test your changes on the pi._


#### Install and start the pigpio daemon on the Raspberry Pi:
_Every time the pi boots up, you must run this in order for the servo to work. We have already added this command to run on startup, but you may want to confirm that it is running, e.g. by using `htop`._

```bash
sudo pigpiod
```

#### Install the mscl library to communicate with the IMU:

https://github.com/LORD-MicroStrain/MSCL

(scroll down and click on the Python 3 link for arm64, and then follow [this](https://github.com/LORD-MicroStrain/MSCL/blob/master/HowToUseMSCL.md#python-1) guide.)

### Project Structure


```
AirbrakesV2/
├── airbrakes/
|   ├── hardware/
│   │   ├── [files related to the connection of the pi with hardware ...]
|   ├── data_handling/
│   │   ├── [files related to the processing of data ...]
│   ├── [files which control the airbrakes at a high level ...]
├── tests/  [used for testing all the code]
│   ├── ...
├── logs/  [log files made by the logger]
│   ├── log_1.csv
├── scripts/  [small files to test individual components like the servo]
│   ├── ...
├── main.py [main file used to run on the rocket]
├── constants.py [file for constants used in the project]
├── pyproject.toml [configuration file for the project]
├── README.md
```

### Running Tests
Our CI pipeline uses [pytest](https://pytest.org) to run tests. You can run the tests locally to ensure that your changes are working as expected.

To run the tests, run this command from the project root directory:
```pytest```

If you make a change to the code, please make sure to update or add the necessary tests.

### Running the Linter

Our CI also tries to maintain code quality by running a linter. We use [Ruff](https://docs.astral.sh/ruff/).

To run the linter, and fix any issues it finds, run:
```ruff check . --fix --unsafe-fixes```

To format the code, run:
```ruff format .```


### Usage
To run the main program, simply run:
```python3 main.py```

However during development, you may want to run individual scripts to test components. For example, to test the servo, run:
```python3 -m scripts.run_servo```

To run a simulation, make sure to first specify the path to the csv file in `constants.py` and then run:
```python3 main.py m```

This will run the program with the mock data, with values of the simulation printed in real time. You many need to adjust `mock_imu.py` according to the data structure of the csv file.

If you want to connect to the servo so you can see extension in realtime, run
```python3 main.py m rs```

### Contributing
Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

### License
This project is licensed under the MIT License. You are free to copy, distribute, and modify the software, provided that the original license notice is included in all copies or substantial portions of the software. See LICENSE for more.
