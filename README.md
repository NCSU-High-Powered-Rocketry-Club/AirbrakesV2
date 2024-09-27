# AirbrakesV2


## Overview
This project controls the extension of airbrakes using a servo motor. It includes modules for logging data and managing the servo motor.

### Installation

#### Install uv:

[uv](https://docs.astral.sh/uv/getting-started/installation/) is a python and project manager, which makes handling different python versions and virtual enviornments easier.

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

#### Install and start the pigpio daemon on the Raspberry Pi:
*Every time the pi boots up, you must run this in order for the servo to work. We have already added this command to run on startup, but you may want to confirm that it is running, e.g. by using `htop`.

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
```python3 main.py mock```

This will run the program with the mock data, with values of the simulation printed in real time. You many need to adjust `mock_imu.py` according to the data structure of the csv file.

### Contributing
Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.
