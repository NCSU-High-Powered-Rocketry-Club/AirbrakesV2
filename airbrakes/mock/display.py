"""File to handle the display of real-time flight data in the terminal."""

import multiprocessing
import time
from typing import TYPE_CHECKING, Literal

import psutil
from colorama import Fore, Style, init

if TYPE_CHECKING:
    from airbrakes.airbrakes import AirbrakesContext


# Shorten colorama names, I (jackson) don't love abbreviations but this is a lot of typing and
# ruff doesn't like when the lines are too long and they are ugly when long (harshil)
G = Fore.GREEN
R = Fore.RED
Y = Fore.YELLOW
RESET = Style.RESET_ALL


class FlightDisplay:
    """Class related to displaying real-time flight data in the terminal with pretty colors
    and spacing.
    """

    # Initialize Colorama
    MOVE_CURSOR_UP = "\033[F"  # Move cursor up one line
    NATURAL_END = "natural"
    INTERRUPTED_END = "interrupted"

    __slots__ = ("airbrakes", "processes", "start_time")

    def __init__(self, airbrakes: "AirbrakesContext", start_time: float) -> None:
        """
        :param airbrakes: The AirbrakesContext object.
        :param start_time: The time (in seconds) the simulation started.
        """
        init(autoreset=True)  # Automatically reset colors after each print
        self.airbrakes = airbrakes
        self.start_time = start_time
        # Prepare the processes for monitoring in the simulation:
        self.processes = self.prepare_process_dict()

    def update_display(self, end_sim: Literal["natural", "interrupted"] | bool = False) -> None:
        """
        Updates the display with real-time data.
        :param end_sim: Whether the simulation ended or was interrupted.
        """
        try:
            current_queue_size = self.airbrakes.imu._data_queue.qsize()
        except NotImplementedError:  # Returns NotImplementedError on arm architecture (Raspberry Pi)
            current_queue_size = "N/A"

        # Prepare output
        data_processor = self.airbrakes.data_processor
        apogee_predictor = self.airbrakes.apogee_predictor
        output = [
            f"{Y}{'=' * 12} REAL TIME FLIGHT DATA {'=' * 12}{RESET}",
            f"Time since sim start:      {G}{time.time() - self.start_time:<10.2f}{RESET} {R}s{RESET}",
            f"State:                     {G}{self.airbrakes.state.name:<15}{RESET}",
            f"Current velocity:          {G}{data_processor.vertical_velocity:<10.2f}{RESET} {R}m/s{RESET}",
            f"Max speed so far:          {G}{data_processor.max_vertical_velocity:<10.2f}{RESET} {R}m/s{RESET}",
            f"Current height:            {G}{data_processor.current_altitude:<10.2f}{RESET} {R}m{RESET}",
            f"Max height so far:         {G}{data_processor.max_altitude:<10.2f}{RESET} {R}m{RESET}",
            f"Airbrakes extension:       {G}{self.airbrakes.current_extension.value}{RESET}",
            f"IMU Data Queue Size:       {G}{current_queue_size}{RESET}",
            f"Predicted Apogee:          {G}{apogee_predictor.apogee:<20.2f}{RESET} {R}m{RESET}",
            f"{Y}{'=' * 13} REAL TIME CPU LOAD {'=' * 14}{RESET}",
        ]

        # Add CPU usage data with color coding
        for name, process in self.processes.items():
            # interval=None can result in inaccurate readings (it might show > 100%), but we don't
            # need high accuracy
            cpu_usage = process.cpu_percent(interval=None)
            if cpu_usage < 50:
                cpu_color = G
            elif cpu_usage < 75:
                cpu_color = Y
            else:
                cpu_color = R
            output.append(f"{name:<25}    {cpu_color}CPU Usage: {cpu_usage:>6.2f}% {RESET}")

        # Print the output
        print("\n".join(output))

        # Move the cursor up for the next update, if the simulation hasn't ended:
        if not end_sim:
            print(self.MOVE_CURSOR_UP * len(output), end="", flush=True)

        # Print the end of simulation message if the simulation has ended
        if end_sim == self.NATURAL_END:
            # Print the end of simulation header
            print(f"{R}{'=' * 14} END OF SIMULATION {'=' * 14}{RESET}")
        elif end_sim == self.INTERRUPTED_END:
            print(f"{R}{'=' * 12} INTERRUPTED SIMULATION {'=' * 13}{RESET}")

    def prepare_process_dict(self) -> dict[str, psutil.Process]:
        """
        Prepares a dictionary of processes to monitor CPU usage for.

        :return: A dictionary of process names and their corresponding psutil.Process objects.
        """
        all_processes = {}
        imu_process = self.airbrakes.imu._data_fetch_process
        log_process = self.airbrakes.logger._log_process
        current_process = multiprocessing.current_process()
        for p in [imu_process, log_process, current_process]:
            # psutil allows us to monitor CPU usage of a process, along with low level information
            # which we are not using.
            all_processes[p.name] = psutil.Process(p.pid)
        return all_processes
