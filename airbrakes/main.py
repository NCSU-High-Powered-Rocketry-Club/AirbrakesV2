"""The main file which will be run on the Raspberry Pi. It will create the AirbrakesContext object
and run the main loop."""

from airbrakes.graphics.application import AirbrakesApplication


def run_real_flight() -> None:
    """Entry point for the application to run the real flight. Entered when run with
    `uv run real` or `uvx --from git+... real`."""
    # args = arg_parser()
    # run_flight(args)


def run_mock_flight() -> None:
    """Entry point for the application to run the mock flight. Entered when run with
    `uvx --from git+... mock` or `uv run mock`."""
    # args = arg_parser(mock_invocation=True)
    # run_flight(args)
    app = AirbrakesApplication()
    app.run()


if __name__ == "__main__":
    # Legacy way to run the program:
    # python -m airbrakes.main [ARGS]

    # Command line args (after these are run, you can press Ctrl+C to exit the program):
    # python main.py -v: Shows the display with much more data
    # python main.py -m: Runs a replay on your computer
    # python main.py -m -r: Runs a replay on your computer with the real servo
    # python main.py -m -l: Runs a replay on your computer and keeps the log file after the
    # replay stops
    # python main.py -m -f: Runs a replay on your computer at full speed
    # python main.py -m -d: Runs a replay on your computer in debug mode (doesn't show display)
    # args = arg_parser()
    # main(args)
    app = AirbrakesApplication()
    app.run()
