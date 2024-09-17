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

```pip install -r requirements.txt```

#### Install and start the pigpio daemon on the Raspberry Pi:

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
|   ├── imu/
│   │   ├── [files related to the imu]
│   ├── [files related to airbrakes ...]
├── tests/  [used for testing all the code]
│   ├── ...
├── logs/  [log files made by the logger]
│   ├── log_1.csv
├── scripts/  [small files to test individual components like the servo]
│   ├── ...
├── main.py [main file used to run on the rocket]
├── requirements.txt
├── README.md
```

### Running Tests
To run the tests, use pytest:
```pytest```

### Running the Linter
This project uses ruff for linting. To run the linter, use:
```ruff check . --fix```
```ruff format .```

### Usage
```python3 main.py```

Initialize the Servo:

Set the Servo Extension:

Logging Data:

Contributing
Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

License
This project is licensed under the MIT License. See the LICENSE file for details.