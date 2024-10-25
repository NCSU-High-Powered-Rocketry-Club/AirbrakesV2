"""File to handle the display of real-time flight data in the terminal."""

import multiprocessing
import threading
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

    __slots__ = (
        "_cpu_thread",
        "_cpu_usages",
        "_processes",
        "_thread_target",
        "airbrakes",
        "end_sim_interrupted",
        "end_sim_natural",
        "start_time",
    )

    def __init__(self, airbrakes: "AirbrakesContext", start_time: float) -> None:
        """
        :param airbrakes: The AirbrakesContext object.
        :param start_time: The time (in seconds) the simulation started.
        """
        init(autoreset=True)  # Automatically reset colors after each print
        self.airbrakes = airbrakes
        self.start_time = start_time
        # Prepare the processes for monitoring in the simulation:
        self._processes: dict[str, psutil.Process] | None = None
        self._cpu_usages: dict[str, float] | None = None
        # daemon threads are killed when the main thread exits.
        self._thread_target = threading.Thread(target=self.update_display, daemon=True, name="Real Time Display Thread")
        self._cpu_thread = threading.Thread(target=self.update_cpu_usage, daemon=True, name="CPU Usage Thread")
        # Create events to signal the end of the simulation.
        self.end_sim_natural = threading.Event()
        self.end_sim_interrupted = threading.Event()

    def start(self) -> None:
        """Starts the display and cpu monitoring thread. Also initializes the processes to monitor."""
        # Prepare the processes for monitoring in the simulation:
        # This should only be done after airbrakes.start() is called, because we need the process IDs.
        self._processes = self.prepare_process_dict()
        self._cpu_usages = {name: 0.0 for name in self._processes}
        self._cpu_thread.start()
        self._thread_target.start()

    def stop(self) -> None:
        """Stops the display thread."""
        self._cpu_thread.join()
        self._thread_target.join()

    def update_cpu_usage(self, interval: float = 0.3) -> None:
        """Update CPU usage for each monitored process every `interval` seconds. This is run in
        another thread because polling for CPU usage is a blocking operation."""
        cpu_count = psutil.cpu_count()
        while not self.end_sim_natural.is_set() and not self.end_sim_interrupted.is_set():
            for name, process in self._processes.items():
                # interval=None is not recommended and can be inaccurate.
                # We normalize the CPU usage by the number of CPUs to get average cpu usage, otherwise
                # it's usually > 100%.
                self._cpu_usages[name] = process.cpu_percent(interval=interval) / cpu_count

    def update_display(self) -> None:
        """
        Updates the display with real-time data. Runs in another thread. Automatically stops when the simulation ends.
        """
        while True:
            if self.end_sim_natural.is_set():
                self._update_display(self.NATURAL_END)
                break
            if self.end_sim_interrupted.is_set():
                self._update_display(self.INTERRUPTED_END)
                break
            self._update_display(False)

    def _update_display(self, end_sim: Literal["natural", "interrupted"] | bool = False) -> None:
        """
        Updates the display with real-time data.
        :param end_sim: Whether the simulation ended or was interrupted.
        """
        try:
            current_queue_size = self.airbrakes.imu._data_queue.qsize()
        except NotImplementedError:  # Returns NotImplementedError on arm architecture (Raspberry Pi)
            current_queue_size = "N/A"

        # Prepare output
        output = [
            f"{Y}{'=' * 12} REAL TIME FLIGHT DATA {'=' * 12}{RESET}",
            f"Time since sim start:      {G}{time.time() - self.start_time:<10.2f}{RESET} {R}s{RESET}",
            f"State:                     {G}{self.airbrakes.state.name:<15}{RESET}",
            f"Current speed:             {G}{self.airbrakes.data_processor.speed:<10.2f}{RESET} {R}m/s{RESET}",
            f"Max speed so far:          {G}{self.airbrakes.data_processor.max_speed:<10.2f}{RESET} {R}m/s{RESET}",
            f"Current height:            {G}{self.airbrakes.data_processor.current_altitude:<10.2f}{RESET} {R}m{RESET}",
            f"Max height so far:         {G}{self.airbrakes.data_processor.max_altitude:<10.2f}{RESET} {R}m{RESET}",
            f"Airbrakes extension:       {G}{self.airbrakes.current_extension.value}{RESET}",
            f"IMU Data Queue Size:       {G}{current_queue_size}{RESET}",
            f"{Y}{'=' * 13} REAL TIME CPU LOAD {'=' * 14}{RESET}",
        ]

        # Add CPU usage data with color coding
        for name, cpu_usage in self._cpu_usages.items():
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
