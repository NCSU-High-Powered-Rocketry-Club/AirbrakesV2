"""File to handle the display of real-time flight data in the terminal."""

import os
import threading
import time
from typing import TYPE_CHECKING

from colorama import Fore, Style, init

from airbrakes.constants import DisplayEndingType

if TYPE_CHECKING:
    import argparse

    from airbrakes.context import Context


G = Fore.GREEN
R = Fore.RED
Y = Fore.YELLOW
C = Fore.CYAN
RESET = Style.RESET_ALL


class FlightDisplay:
    """
    Class related to displaying real-time flight data in the terminal with
    pretty colors and spacing.
    """

    MOVE_CURSOR_UP = "\033[F"  # Move cursor up one line

    __slots__ = (
        "_args",
        "_context",
        "_current_pid",
        "_display_header",
        "_display_update_thread",
        "_launch_file",
        "_pitch_at_startup",
        "_running",
        "_start_time",
        "end_mock_interrupted",
        "end_mock_natural",
    )

    def __init__(self, context: Context, args: argparse.Namespace) -> None:
        """
        Initializes the FlightDisplay object.

        :param context: The Context object.
        :param args: Command line arguments determining the program
            configuration.
        """
        init(autoreset=True)  # Automatically reset colors after each print
        self._context = context
        self._start_time = 0.0  # Time since the replay started (first packet received)
        self._running = False
        self._args = args
        self._pitch_at_startup: float = 0.0  # The calculated pitch in degrees in StandbyState

        # daemon threads are killed when the main thread exits.
        self._display_update_thread = threading.Thread(
            target=self.update_display, daemon=True, name="Real Time Display Thread"
        )
        self._current_pid = os.getpid()
        # Create events to signal the end of the replay.
        self.end_mock_natural = threading.Event()
        self.end_mock_interrupted = threading.Event()

        try:
            # Try to get the launch file name (only available in MockFIRM)
            self._launch_file = self._context.firm._log_file_path.name
        except AttributeError:  # If it failed, that means we are running a real flight!
            self._launch_file = "N/A"

        # The string to show at the top of the display:
        self._display_header = f"{Y}{'=' * 15} {'REPLAY' if self._args.mode == 'mock' else 'REAL TIME'} INFO {'=' * 15}{RESET}"  # noqa: E501

    def start(self) -> None:
        """
        Starts the display and cpu monitoring thread.

        Also prepares the processes for monitoring in the replay. This
        should only be done *after* context.start() is called, because
        we need the thread IDs.
        """
        self._running = True
        self._display_update_thread.start()

    def stop(self) -> None:
        """Stops the display thread."""
        self._running = False
        self._display_update_thread.join()

    def sound_alarm_if_imu_is_having_issues(self) -> None:
        """
        Sounds an audible alarm if the IMU has invalid fields or large
        change in velocity.

        This is most useful on real flights, where it is hard to see the
        display due to sunlight.
        """
        has_large_velocity = False
        imu_queue_backlog = False

        # If the absolute value of our velocity is large in standby state, we have a problem:
        if abs(self._context.data_processor.vertical_velocity) > 2:
            has_large_velocity = True

        # If we have too many packets in one iteration, that means the IMU is producing data faster
        # # than we can consume it, which is a problem:
        if self._context.context_data_packet.retrieved_firm_packets > 30:
            imu_queue_backlog = True

        if has_large_velocity or imu_queue_backlog:
            print("\a", end="")  # \a is the bell character, which makes a beep sound

    def update_display(self) -> None:
        """
        Updates the display with real-time data.

        Runs in another thread. Automatically stops when the replay
        ends.
        """
        # Don't print the flight data if we are in debug mode
        if self._args.debug:
            return

        # Wait till we processed a data packet. This is to prevent the display from updating
        # before we have any data to display.
        while not (
            self._context.context_data_packet and self._context.data_processor._last_data_packet
        ):
            pass

        self._start_time = time.time()

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

            time.sleep(0.01)  # Don't hog the CPU

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
        fetched_packets_in_main = self._context.context_data_packet.retrieved_firm_packets

        data_processor = self._context.data_processor

        time_since_launch = (
            self._context.data_processor.current_timestamp_seconds
            - self._context.launch_time_seconds
            if self._context.launch_time_seconds
            else 0
        )

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
            f"Predicted apogee:          {G}{self._context.most_recent_apogee_predictor_data_packet.predicted_apogee if self._context.most_recent_apogee_predictor_data_packet else 0:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
            f"Airbrakes extension:       {G}{self._context.servo.current_extension.value:<10}{RESET} {R}deg{RESET}",  # noqa: E501
        ]

        # Adds additional info to the display if -v was specified
        if self._args.verbose:
            output.extend(
                [
                    f"{Y}{'=' * 18} DEBUG INFO {'=' * 17}{RESET}",
                    f"Average acceleration:            {G}{data_processor.average_vertical_acceleration:<10.2f}{RESET} {R}m/s^2{RESET}",  # noqa: E501
                    f"Predicted apogee:                {G}{self._context.most_recent_apogee_predictor_data_packet.predicted_apogee if self._context.most_recent_apogee_predictor_data_packet else 0:<10.2f}{RESET} {R}m{RESET}",  # noqa: E501
                    f"Fetched packets in Main:         {G}{fetched_packets_in_main:<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    f"Log buffer size:                 {G}{len(self._context.logger._log_buffer):<10}{RESET} {R}packets{RESET}",  # noqa: E501
                    # Use htop -H -p <PID> to see thread CPU usage
                    f"Current process ID:              {G}{self._current_pid:<10}{RESET} ",
                ]
            )

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
