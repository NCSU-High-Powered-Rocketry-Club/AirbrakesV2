# Local setup for the rebels

If you don't want to use `uv`, you can set up the project using Python.

**This project uses Python 3.13. Using an older version may not work since we use newer language features**


### 1. Clone the repository:

```
git clone https://github.com/NCSU-High-Powered-Rocketry-Club/AirbrakesV2.git
cd AirbrakesV2
```

### 2. Set up a virtual environment:

```bash
python -m venv .venv

# For Linux
source .venv/bin/activate
# For Windows
.\.venv\Scripts\activate
```

### 3. Install the required dependencies:

```bash
pip install . -e
```

This command will install the required dependencies for the project. If you want to install the development dependencies, you can run:

```bash
pip install pytest pytest-cov ruff pre-commit
```

Then, follow from [step 3 on the main README](README.md#3-install-the-pre-commit-hook) to finish the local setup and make a commit.


## Advanced Local Usage

The python equivalent command to `uv` is:

```bash
python -m airbrakes.main mock
``` 

for running a mock. So to run a mock sim with the real servo, you would run:

```bash
python -m airbrakes.main mock -r
```

To run a real flight, you would run:

```bash
python -m airbrakes.main real
```

To run a simulation, you would run:

```bash
python -m airbrakes.main sim
```

As always, you can see all the options by running:

```bash
python -m airbrakes.main --help
```

To run the textual app with the console, you would run:

```bash
textual run --dev airbrakes/main.py [options]
```

To run a script for testing, you would run:

```bash
python scripts/run_logger.py
```

_There are libraries that only fully work when running on the Pi (gpiozero, mscl, picamera2), so if you're having trouble importing them locally, program the best you can and test your changes on the pi._