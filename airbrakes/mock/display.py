"""File to handle the display of real-time flight data in the terminal."""

import argparse
import multiprocessing
import threading
import time
from typing import TYPE_CHECKING

import psutil
from colorama import Fore, Style, init

from airbrakes.constants import DisplayEndingType

if TYPE_CHECKING:
    from airbrakes.context import Context


G = Fore.GREEN
R = Fore.RED
Y = Fore.YELLOW
C = Fore.CYAN
RESET = Style.RESET_ALL


class FlightDisplay:
    """
    Class related to displaying real-time flight data in the terminal with pretty colors
    and spacing.
    """

    MOVE_CURSOR_UP = "\033[F"  # Move cursor up one line

    __slots__ = (
        "_apogee_at_convergence",
        "_args",
        "_coast_time_ns",
        "_context",
        "_convergence_height",
        "_convergence_time_seconds",
        "_cpu_thread",
        "_cpu_usages",
        "_display_header",
        "_launch_file",
        "_launch_time_ns",
        "_pitch_at_startup",
        "_processes",
        "_running",
        "_start_time",
        "_thread_target",
        "_verbose",
        "end_mock_interrupted",
        "end_mock_natural",
    )

    def __init__(self, context: "Context", start_time: float, args: argparse.Namespace) -> None:
        """
        Initializes the FlightDisplay object.
        :param conetxt: The AirbrakesContext object.
        :param start_time: The time (in seconds) the replay started.
        :param args: Command line arguments determining the program configuration.
        """
        init(autoreset=True)  # Automatically reset colors after each print
        self._context = context
        self._start_time = start_time
        self._running = False
        self._args = args
        self._launch_time_ns: int = 0  # Launch time from MotorBurnState
        self._coast_time_ns: int = 0  # Coast time from CoastState
        self._convergence_time_seconds: float = 0.0  # Time to convergence of apogee from CoastState
        self._convergence_height: float = 0.0  # Height at convergence of apogee from CoastState
        self._pitch_at_startup: float = 0.0  # The calculated pitch in degrees in StandbyState
        self._apogee_at_convergence: float = 0.0  # Apogee at prediction convergence from CoastState

        # Prepare the processes for monitoring in the replay:
        self._processes: dict[str, psutil.Process] | None = None
        self._cpu_usages: dict[str, float] | None = None
        # daemon threads are killed when the main thread exits.
        self._thread_target = threading.Thread(
            target=self.update_display, daemon=True, name="Real Time Display Thread"
        )
        self._cpu_thread = threading.Thread(
            target=self.update_cpu_usage, daemon=True, name="CPU Usage Thread"
        )
        # Create events to signal the end of the replay.
        self.end_mock_natural = threading.Event()
        self.end_mock_interrupted = threading.Event()

        try:
            # Try to get the launch file name (only available in MockIMU or SimIMU)
            self._launch_file = self._context.imu._log_file_path.name
        except AttributeError:  # If it failed, that means we are running a real flight!
            self._launch_file = "N/A"

        # The string to show at the top of the display:
        self._display_header = f"{Y}{'=' * 15} {'REPLAY' if self._args.mode == 'mock' else 'REAL TIME'} INFO {'=' * 15}{RESET}"  # noqa: E501

    def start(self) -> None:
        """
        Starts the display and cpu monitoring thread. Also prepares the processes for monitoring
        in the replay. This should only be done *after* context.start() is called, because we
        need the process IDs.
        """
        self._running = True
        self._processes = self.prepare_process_dict()
        self._cpu_usages = {name: 0.0 for name in self._processes}
        self._cpu_thread.start()
        self._thread_target.start()

    def stop(self) -> None:
        """
        Stops the display thread. Similar to start(), this must be called *before*
        context.stop() is called to prevent psutil from raising a NoSuchProcess exception.
        """
        self._running = False
        self._cpu_thread.join()
        self._thread_target.join()

    def update_cpu_usage(self, interval: float = 0.3) -> None:
        """
        Update CPU usage for each monitored process every `interval` seconds. This is run in
        another thread because polling for CPU usage is a blocking operation.
        :param interval: time in seconds between polling CPU usage.
        """
        cpu_count = psutil.cpu_count()
        while self._running:
            for name, process in self._processes.items():
                # interval=None is not recommended and can be inaccurate.
                # We normalize the CPU usage by the number of CPUs to get average cpu usage,
                # otherwise it's usually > 100%.
                try:
                    self._cpu_usages[name] = process.cpu_percent(interval=interval) / cpu_count
                except psutil.NoSuchProcess:
                    # The process has ended, so we set the CPU usage to 0.
                    self._cpu_usages[name] = 0.0

    def sound_alarm_if_imu_is_having_issues(self) -> None:
        """
        Sounds an audible alarm if the IMU has invalid fields or large change in velocity. This is
        most useful on real flights, where it is hard to see the display due to sunlight.
        """
        has_invalid_fields = False
        has_large_velocity = False
        imu_queue_backlog = False
        pitch_drift = False

        # If the absolute value of our velocity is large in standby state, we have a problem:
        if abs(self._context.data_processor.vertical_velocity) > 2:
            has_large_velocity = True

        # While normally it is bad practice to access private variables, we kind of consider the
        # display outside of/an addon to the main program, so we are okay with it here.
        invalid_fields = self._context.data_processor._last_data_packet.invalid_fields
        has_invalid_fields = bool(invalid_fields)

        if self._context.imu.imu_packets_per_cycle > 30:
            imu_queue_backlog = True

        if (
            self._pitch_at_startup
            and abs(self._context.data_processor.average_pitch - self._pitch_at_startup) > 1
        ):
            pitch_drift = True

        if has_invalid_fields or has_large_velocity or imu_queue_backlog or pitch_drift:
            print("\a", end="")  # \a is the bell character, which makes a beep sound

    def update_display(self) -> None:
        """
        Updates the display with real-time data. Runs in another thread. Automatically stops when
        the replay ends.
        """
        # Don't print the flight data if we are in debug mode
        if self._args.debug:
            return

        # Wait till we processed a data packet. This is to prevent the display from updating
        # before we have any data to display.
        while not self._context.data_processor._last_data_packet:
            pass

        # Update the display as long as the program is running:
        while self._running:
            self._update_display()

            # If we are running a real flight, check if there is any cause of concern:
            if self._args.mode == "real":
                self.sound_alarm_if_imu_is_having_issues()
                # We will stop the display when the rocket takes off (performance reasons)
                if self._context.state.name == "MotorBurnState":
                    self._update_display(DisplayEndingType.TAKEOFF)
                    break

        # The program has ended, so we print the final display, depending on how it ended:
        if self.end_mock_natural.is_set():
            self._update_display(DisplayEndingType.NATURAL)
        if self.end_mock_interrupted.is_set():
            self._update_display(DisplayEndingType.INTERRUPTED)

    def _update_display(self, end_type: DisplayEndingType | None = None) -> None:
        """
        Updates the display with real-time data.
        :param end_type: The type of ending for the flight data display.
        """
        current_queue_size = self._context.imu.queued_imu_packets
        fetched_packets_in_main = self._context.context_data_packet.retrieved_imu_packets
        fetched_packets_from_imu = (
            self._context.imu.imu_packets_per_cycle if self._args.mode == "real" else "N/A"
        )

        data_processor = self._context.data_processor

        invalid_fields = data_processor._last_data_packet.invalid_fields
        if invalid_fields:
            invalid_fields = f"{RESET}{R}{invalid_fields}{R}{RESET}"

        # Set the launch time if it hasn't been set yet:
        if not self._launch_time_ns and self._context.state.name == "MotorBurnState":
            self._launch_time_ns = self._context.state.start_time_ns

        elif not self._coast_time_ns and self._context.state.name == "CoastState":
            self._coast_time_ns = self._context.state.start_time_ns

        if self._launch_time_ns:
            time_since_launch = (
                self._context.data_processor.current_timestamp - self._launch_time_ns
            ) * 1e-9
        else:
            time_since_launch = 0

        if (
            self._coast_time_ns
            and not self._convergence_time_seconds
            and self._context.last_apogee_predictor_packet.predicted_apogee
        ):
            self._convergence_time_seconds = (
                data_processor.current_timestamp - self._coast_time_ns
            ) * 1e-9
            self._convergence_height = data_processor.current_altitude
            self._apogee_at_convergence = (
                self._context.last_apogee_predictor_packet.predicted_apogee
            )

        # Assign the startup pitch value when it is available:
        if not self._pitch_at_startup:
            self._pitch_at_startup = data_processor.average_pitch

        # Prepare output
        output = [
            self._display_header,
            f"Replay file:                  {C}{self._launch_file}{RESET}",
            f"Time since replay start:      {C}{time.time() - self._start_time:<10.2f}{RESET} {R}s{RESET}",  # noqa: E501
            f"{Y}{'=' * 12} REAL TIME FLIGHT DATA {'=' * 12}{RESET}",
            # Format time as MM:SS:
            f"Launch time:               {G}T+{time.strftime('%M:%S', time.gmtime(time_since_launch))}{RESET}",  # noqa: E501
            f"State:                     {G}{self._context.state.name:<15}{RESET}",
            f"Current velocity:          {G}{data_processor.vertical_velocity:<10.2f}{RESET} {R}m/s{RESET}",  # noqa: E501
            f"Max velocity so far:       {G}{data_processor.max_vertical_velocity:<10.2f}{RESET} {R}m/s{RESET}",  # noqa: E501
            f"Current height:            {G}{data_processor.current_altitude:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
            f"Max height so far:         {G}{data_processor.max_altitude:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
            f"Predicted Apogee:          {G}{self._context.last_apogee_predictor_packet.predicted_apogee:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
            f"Airbrakes extension:       {G}{self._context.servo.current_extension.value:<10}{RESET} {R}deg{RESET}",  # noqa: E501
        ]

        # Adds additional info to the display if -v was specified
        if self._args.verbose:
            output.extend(
                [
                    f"{Y}{'=' * 18} DEBUG INFO {'=' * 17}{RESET}",
                    f"Average pitch:                   {G}{data_processor.average_pitch:<10.2f}{RESET} {R}deg{RESET}",  # noqa: E501
                    f"Average acceleration:            {G}{data_processor.average_vertical_acceleration:<10.2f}{RESET} {R}m/s^2{RESET}",  # noqa: E501
                    f"Convergence Time:                {G}{self._convergence_time_seconds:<10.2f}{RESET} {R}s{RESET}",  # noqa: E501
                    f"Convergence Height:              {G}{self._convergence_height:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
                    f"Predicted apogee at Convergence: {G}{self._apogee_at_convergence:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
                    f"IMU Data Queue Size:             {G}{current_queue_size:<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    f"Fetched packets in Main:         {G}{fetched_packets_in_main:<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    f"Fetched packets from IMU:        {G}{fetched_packets_from_imu:<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    f"Log buffer size:                 {G}{len(self._context.logger._log_buffer):<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    f"Invalid fields:                  {G}{invalid_fields!s:<25}{G}{RESET}",
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

        # Move the cursor up for the next update, if the replay hasn't ended:
        if not end_type:
            print(self.MOVE_CURSOR_UP * len(output), end="", flush=True)

        # Print the end of replay message if the replay has ended
        match end_type:
            case DisplayEndingType.NATURAL:
                print(f"{R}{'=' * 14} END OF REPLAY {'=' * 14}{RESET}")
            case DisplayEndingType.INTERRUPTED:
                print(f"{R}{'=' * 12} INTERRUPTED REPLAY {'=' * 13}{RESET}")
            case DisplayEndingType.TAKEOFF:
                print(f"{R}{'=' * 13} ROCKET LAUNCHED {'=' * 14}{RESET}")

    def prepare_process_dict(self) -> dict[str, psutil.Process]:
        """
        Prepares a dictionary of processes to monitor CPU usage for.
        :return: A dictionary of process names and their corresponding psutil.Process objects.
        """
        all_processes = {}
        imu_process = self._context.imu._data_fetch_process
        log_process = self._context.logger._log_process
        apogee_process = self._context.apogee_predictor._prediction_process
        # camera_process = self._context.camera.camera_control_process
        current_process = multiprocessing.current_process()
        for p in [imu_process, log_process, current_process, apogee_process]:
            # psutil allows us to monitor CPU usage of a process, along with low level information
            # which we are not using.
            all_processes[p.name] = psutil.Process(p.pid)
        return all_processes
