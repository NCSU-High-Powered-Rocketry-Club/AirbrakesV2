"""Module to handle recording of the airbrakes with a camera."""

import os
import signal
import time
from contextlib import suppress
from multiprocessing import Event, Process

from airbrakes.constants import CAMERA_IDLE_TIMEOUT_SECONDS, CAMERA_SAVE_PATH

# These libraries are only available on the Raspberry Pi so we ignore them if they are not available
with suppress(ImportError):
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import CircularOutput


class Camera:
    """
    This is the class used to interact with the camera on our rocket. It records on a separate
    process.
    """

    __slots__ = ("camera_control_process", "motor_burn_started", "stop_context_event")

    def __init__(self):
        self.stop_context_event = Event()
        self.motor_burn_started = Event()
        self.camera_control_process = Process(
            target=self._camera_control_loop, name="Camera process"
        )

    @property
    def is_running(self):
        """Returns whether the camera is currently recording."""
        return self.camera_control_process.is_alive()

    def start(self):
        """Start the video recording, with a buffer. This starts recording in a different process"""
        self.camera_control_process.start()

    def stop(self):
        """Stop the video recording."""
        self.motor_burn_started.set()  # in case we stop before motor burn
        self.stop_context_event.set()
        self.camera_control_process.join()

    def start_recording(self):
        """Start recording when motor burn has started."""
        self.motor_burn_started.set()

    # ------------------------ ALL METHODS BELOW RUN IN A SEPARATE PROCESS -------------------------
    def _camera_control_loop(self):  # pragma: no cover
        """Controls the camera recording process."""
        # Ignore the SIGINT (Ctrl+C) signal, because we only want the main process to handle it
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignores the interrupt signal

        # set logging level-
        os.environ["LIBCAMERA_LOG_LEVELS"] = "ERROR"

        camera = Picamera2()
        # Make the camera look good in daylight:
        camera.set_controls({"AwbEnable": True, "AwbMode": "Daylight"})
        # We use the H264 encoder and a circular output to save the video to a file.
        encoder = H264Encoder()
        # The circular output is a buffer with a default size of 150 bytes? which according to
        # the docs is enough for 5 seconds of video at 30 fps.
        output = CircularOutput()
        # Create a basic video configuration
        camera.configure(camera.create_video_configuration())

        # Start recording with the buffer. This operation is non-blocking.
        camera.start_recording(encoder, output)

        # TODO: this is ass
        # Check if motor burn has started, if it has, we can stop buffering and start saving
        # the video. This way we get a few seconds of video before liftoff too. Otherwise, just
        # sleep and wait.
        while not self.motor_burn_started.is_set():
            # Unfortunately, an `multiprocessing.Event.wait()` doesn't seem to work, hence this
            # ugly while loop instead.
            time.sleep(CAMERA_IDLE_TIMEOUT_SECONDS)

        output.fileoutput = CAMERA_SAVE_PATH
        output.start()

        # Keep recording until we have landed:
        while not self.stop_context_event.is_set():
            time.sleep(CAMERA_IDLE_TIMEOUT_SECONDS)

        output.stop()
