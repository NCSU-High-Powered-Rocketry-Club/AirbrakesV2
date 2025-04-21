"""
Module which uses a mock camera, since the original camera needs many libraries and actual hardware.
"""

import signal
from time import sleep

from airbrakes.constants import BYTES_PER_0_1_SECONDS
from airbrakes.hardware.camera import Camera


class MockCamera(Camera):
    """
    Mocks the camera class.

    This class fills an internal buffer with random bytes
    to simulate a real flight. The number of bytes written correspond to a ~24 fps recording.
    Even though this is detached from the actual camera implementation, using a buffer serves
    some purposes:
    1. Tests CPU and memory load, as this is another process.
    2. Tests that the stop events are working correctly with them.
    """

    __slots__ = ("_buffer",)

    def __init__(self) -> None:
        super().__init__()
        self.camera_control_process.name = "Mock Camera process"
        # The buffer to hold the video data.
        self._buffer = bytearray()

    def _camera_control_loop(self) -> None:
        """
        Starts the mock camera process.
        """
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # Wait for the motor burn to start before starting to write to the buffer.
        self.motor_burn_started.wait()

        # our video is 1280x720, roughly 24 fps, 2 bytes per pixel (?). We get about 9 MB video
        # every ~30 seconds.
        while not self.stop_context_event.is_set():
            # Write CAMERA_IDLE_TIMEOUT_SECONDS seconds of video data to the buffer.

            self._buffer.extend(b"0" * int(BYTES_PER_0_1_SECONDS))
            sleep(0.1)
