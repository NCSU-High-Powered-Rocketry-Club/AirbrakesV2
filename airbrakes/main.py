"""
The main file which will be run on the Raspberry Pi.

It will create the Context object and run the main loop.
"""

import sys

from airbrakes.graphics.application import AirbrakesApplication
from airbrakes.utils import arg_parser


def run_real_flight() -> None:
    """
    Entry point for the application to run the real flight.

    Entered when run with
    `uv run real` or `uvx --from git+... real`.
    """
    # Modify sys.argv to include real as the first argument:
    sys.argv.insert(1, "real")
    args = arg_parser()
    app = AirbrakesApplication(cmd_args=args)
    app.run()


def run_mock_flight() -> None:
    """
    Entry point for the application to run the mock flight.

    Entered when run with
    `uvx --from git+... mock` or `uv run mock`.
    """
    # Modify sys.argv to include mock as the first argument:
    sys.argv.insert(1, "mock")
    args = arg_parser()
    app = AirbrakesApplication(cmd_args=args)
    app.run()


if __name__ == "__main__":
    # Deprecated way to run the program:
    # python -m airbrakes.main [ARGS]

    # The main Airbrakes program can be run in different modes:

    # `uv run real [ARGS]`: Runs the flight with real hardware. Optional arguments:
    #     -s, --mock-servo   : Uses a mock servo instead of the real one.
    #     -c, --mock-camera  : Uses a mock camera instead of the real one.

    # `uv run mock [ARGS]`: Runs the program in mock replay mode, using pre-recorded flight data.
    #   Optional arguments include:
    #     -s, --real-servo   : Uses the real servo instead of a mock one.
    #     -c, --real-camera  : Uses the real camera instead of a mock one.
    #     -f, --fast-replay  : Runs the replay at full speed instead of real-time.
    #     -p, --path <file>  : Specifies a flight data file to use (default is the first file).

    # `uv run sim [ARGS]`: Runs a flight simulation alongside the mock replay.
    #   Optional arguments include:
    #     -s, --real-servo   : Uses the real servo instead of a mock one.
    #     -c, --real-camera  : Uses the real camera instead of a mock one.
    #     -f, --fast-replay  : Runs the simulation at full speed instead of real-time.
    #     preset             : Specifies a preset (full-scale, sub-scale, etc).

    # Global options for all modes:
    #     -d, --debug   : Runs without a display, allowing inspection of print statements.
    #     -v, --verbose : Enables a detailed display with more flight data.

    app = AirbrakesApplication()
    app.run()
