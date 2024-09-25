# AirbrakesV2


## Overview
This project controls the extension of airbrakes using a servo motor. It includes modules for logging data and managing the servo motor.

### Installation
Clone the repository:

```
git clone https://github.com/yourusername/AirbrakesV2.git
cd AirbrakesV2
```

#### Set up a virtual environment:

```
python3 -m venv venv
source venv/bin/activate
```

#### Install the required dependencies:

```pip install .[dev]```

#### Install and start the pigpio daemon on the Raspberry Pi:
*Every time the pi boots up, you must run this in order for the servo to work

```bash
sudo pigpiod
```

#### Install the mscl library to communicate with the IMU:

https://github.com/LORD-MicroStrain/MSCL

(scroll down and click on the Python 3 link for armhf (raspbian))

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

### Contributing
Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.
