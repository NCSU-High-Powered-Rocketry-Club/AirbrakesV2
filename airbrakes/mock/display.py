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
C = Fore.CYAN
RESET = Style.RESET_ALL


class FlightDisplay:
    """Class related to displaying real-time flight data in the terminal with pretty colors
    and spacing.
    """

    # Initialize Colorama
    MOVE_CURSOR_UP = "\033[F"  # Move cursor up one line
    NATURAL_END = "natural"
    INTERRUPTED_END = "interrupted"
    STANDBY_END = "standby"

    __slots__ = (
        "_airbrakes",
        "_coast_time",
        "_convergence_height",
        "_convergence_time",
        "_cpu_thread",
        "_cpu_usages",
        "_launch_file",
        "_simulation_launch_time",
        "_t_minus_launch_time",
        "_mock",
        "_processes",
        "_start_time",
        "_thread_target",
        "_verbose",
        "end_sim_interrupted",
        "end_sim_natural",
    )

    def __init__(
        self, airbrakes: "AirbrakesContext", start_time: float, mock: bool, verbose: bool
    ) -> None:
        """
        :param airbrakes: The AirbrakesContext object.
        :param start_time: The time (in seconds) the simulation started.
        """
        init(autoreset=True)  # Automatically reset colors after each print
        self._airbrakes = airbrakes
        self._start_time = start_time
        self._mock = mock
        self._verbose = verbose
        self._simulation_launch_time: int = 0  # Launch time from MotorBurnState
        self._t_minus_launch_time: int = 0  # T-0 time from StandbyState
        self._coast_time: int = 0  # Coast time from CoastState
        self._convergence_time: float = 0.0  # Time to convergence of apogee from CoastState
        self._convergence_height: float = 0.0  # Height at convergence of apogee from CoastState
        # Prepare the processes for monitoring in the simulation:
        self._processes: dict[str, psutil.Process] | None = None
        self._cpu_usages: dict[str, float] | None = None
        # daemon threads are killed when the main thread exits.
        self._thread_target = threading.Thread(
            target=self.update_display, daemon=True, name="Real Time Display Thread"
        )
        self._cpu_thread = threading.Thread(
            target=self.update_cpu_usage, daemon=True, name="CPU Usage Thread"
        )
        # Create events to signal the end of the simulation.
        self.end_sim_natural = threading.Event()
        self.end_sim_interrupted = threading.Event()

        try:
            # Try to get the launch file name (only available in MockIMU)
            self._launch_file = self._airbrakes.imu._log_file_path.name
        except AttributeError:  # If it failed, that means we are running a real flight!
            self._launch_file = "N/A"

    def start(self) -> None:
        """Starts the display and cpu monitoring thread. Also prepares the processes for monitoring
        in the simulation. This should only be done *after* airbrakes.start() is called, because we
        need the process IDs.
        """
        self._processes = self.prepare_process_dict()
        self._cpu_usages = {name: 0.0 for name in self._processes}
        self._cpu_thread.start()
        self._thread_target.start()

    def stop(self) -> None:
        """Stops the display thread. Similar to start(), this must be called *before*
        airbrakes.stop() is called to prevent psutil from raising a NoSuchProcess exception.
        """
        self._cpu_thread.join()
        self._thread_target.join()

    def update_cpu_usage(self, interval: float = 0.3) -> None:
        """Update CPU usage for each monitored process every `interval` seconds. This is run in
        another thread because polling for CPU usage is a blocking operation."""
        cpu_count = psutil.cpu_count()
        while not self.end_sim_natural.is_set() and not self.end_sim_interrupted.is_set():
            for name, process in self._processes.items():
                # interval=None is not recommended and can be inaccurate.
                # We normalize the CPU usage by the number of CPUs to get average cpu usage,
                # otherwise it's usually > 100%.
                try:
                    self._cpu_usages[name] = process.cpu_percent(interval=interval) / cpu_count
                except psutil.NoSuchProcess:
                    # The process has ended, so we set the CPU usage to 0.
                    self._cpu_usages[name] = 0.0

    def update_display(self) -> None:
        """
        Updates the display with real-time data. Runs in another thread. Automatically stops when
        the simulation ends.
        """
        while True:
            if self.end_sim_natural.is_set():
                self._update_display(self.NATURAL_END)
                break
            if self.end_sim_interrupted.is_set():
                self._update_display(self.INTERRUPTED_END)
                break
            if not self._mock and self._airbrakes.state.name == "MotorBurnState":
                self._update_display(self.STANDBY_END)
                break
            self._update_display(False)

    def calculate_launch_time(self) -> int | None:
        """
        Calculates the launch time of the simulation.
        :return: The launch time of the simulation.
        """
        # Just update our launch time, if it was set:
        if self._simulation_launch_time:
            current_timestamp = self._airbrakes.data_processor.current_timestamp
            return current_timestamp - self._simulation_launch_time

        # Just update our T-minus launch time, if it is a mock, and it was set:
        if self._args.mock and self._t_minus_launch_time:
            current_timestamp = self._airbrakes.data_processor.current_timestamp
            return current_timestamp - self._t_minus_launch_time

        # No launch time set yet, and we are in MotorBurnState:
        if not self._simulation_launch_time and self._airbrakes.state.name == "MotorBurnState":
            self._simulation_launch_time = self._airbrakes.state.start_time_ns
            # Discard the pre-calculated motor burn time, since we have the real one now:
            self._t_minus_launch_time = 0
            return self._simulation_launch_time

        # We are before launch (T-0)
        if self._args.mock and not self._simulation_launch_time and not self._t_minus_launch_time:
            current_timestamp = self._airbrakes.data_processor.current_timestamp
            if current_timestamp is None:
                return None
            pre_calculated_motor_burn_time = self._airbrakes.imu.get_launch_time()
            self._t_minus_launch_time = current_timestamp - pre_calculated_motor_burn_time
            return self._t_minus_launch_time

        return None

    def _update_display(
        self, end_sim: Literal["natural", "interrupted", "standby"] | bool = False
    ) -> None:
        """
        Updates the display with real-time data.
        :param end_sim: Whether the simulation ended or was interrupted.
        """
        try:
            current_queue_size = self._airbrakes.imu._data_queue.qsize()
        except NotImplementedError:
            # Returns NotImplementedError on arm architecture (Raspberry Pi)
            current_queue_size = "N/A"

        fetched_packets = len(self._airbrakes.imu_data_packets)

        data_processor = self._airbrakes.data_processor
        apogee_predictor = self._airbrakes.apogee_predictor

        # Set the actual launch time if it hasn't been set yet:
        launch_clock = self.calculate_launch_time()
        # Format as T-MM:SS:ms if the launch_clock < 0, else format as T+MM:SS:ms
        if launch_clock is not None:
            launch_clock = abs(launch_clock)
            launch_time = time.strftime("%M:%S", time.gmtime(launch_clock))
            launch_time = f"T+{launch_time}" if self._simulation_launch_time else f"T-{launch_time}"
        else:
            launch_time = "N/A"
        print(launch_time)

        if not self._coast_time and self._airbrakes.state.name == "CoastState":
            self._coast_time = self._airbrakes.state.start_time_ns

        if self._simulation_launch_time:
            time_since_launch = (
                self._airbrakes.data_processor.current_timestamp - self._simulation_launch_time
            ) * 1e-9
        else:
            time_since_launch = 0

        if (
            self._coast_time
            and not self._convergence_time
            and self._airbrakes.apogee_predictor.apogee
        ):
            self._convergence_time = (
                self._airbrakes.data_processor.current_timestamp - self._coast_time
            ) * 1e-9
            self._convergence_height = data_processor.current_altitude

        # Prepare output
        output = [
            f"{Y}{'=' * 15} SIMULATION INFO {'=' * 15}{RESET}",
            f"Sim file:                  {C}{self._launch_file}{RESET}",
            f"Time since sim start:      {C}{time.time() - self._start_time:<10.2f}{RESET} {R}s{RESET}",  # noqa: E501
            f"{Y}{'=' * 12} REAL TIME FLIGHT DATA {'=' * 12}{RESET}",
            # Format time as MM:SS:
            f"Launch time:               {G}T+{time.strftime('%M:%S', time.gmtime(time_since_launch))}{RESET}",  # noqa: E501
            f"State:                     {G}{self._airbrakes.state.name:<15}{RESET}",
            f"Current velocity:          {G}{data_processor.vertical_velocity:<10.2f}{RESET} {R}m/s{RESET}",  # noqa: E501
            f"Max velocity so far:       {G}{data_processor.max_vertical_velocity:<10.2f}{RESET} {R}m/s{RESET}",  # noqa: E501
            f"Current height:            {G}{data_processor.current_altitude:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
            f"Max height so far:         {G}{data_processor.max_altitude:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
            f"Predicted Apogee:          {G}{apogee_predictor.apogee:<10.2f}{RESET} {R}m{RESET}",
            f"Airbrakes extension:       {G}{self._airbrakes.current_extension.value}{RESET}",
        ]

        # Adds additional info to the display if -v was specified
        if self._verbose:
            output.extend(
                [
                    f"{Y}{'=' * 18} DEBUG INFO {'=' * 17}{RESET}",
                    f"Convergence Time:          {G}{self._convergence_time:<10.2f}{RESET} {R}s{RESET}",  # noqa: E501
                    f"Convergence Height:        {G}{self._convergence_height:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
                    f"IMU Data Queue Size:       {G}{current_queue_size:<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    f"Fetched packets:           {G}{fetched_packets:<10}{RESET} {R}packets{RESET}",
                    f"Log buffer size:           {G}{len(self._airbrakes.logger._log_buffer):<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    f"{Y}{'=' * 13} REAL TIME CPU LOAD {'=' * 14}{RESET}",
                ]
            )

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
        match end_sim:
            case self.NATURAL_END:
                print(f"{R}{'=' * 14} END OF SIMULATION {'=' * 14}{RESET}")
            case self.INTERRUPTED_END:
                print(f"{R}{'=' * 12} INTERRUPTED SIMULATION {'=' * 13}{RESET}")
            case self.STANDBY_END:
                print(f"{R}{'=' * 13} ROCKET LAUNCHED {'=' * 14}{RESET}")

    def prepare_process_dict(self) -> dict[str, psutil.Process]:
        """
        Prepares a dictionary of processes to monitor CPU usage for.
        :return: A dictionary of process names and their corresponding psutil.Process objects.
        """
        all_processes = {}
        imu_process = self._airbrakes.imu._data_fetch_process
        log_process = self._airbrakes.logger._log_process
        apogee_process = self._airbrakes.apogee_predictor._prediction_process
        current_process = multiprocessing.current_process()
        for p in [imu_process, log_process, current_process, apogee_process]:
            # psutil allows us to monitor CPU usage of a process, along with low level information
            # which we are not using.
            all_processes[p.name] = psutil.Process(p.pid)
        return all_processes
