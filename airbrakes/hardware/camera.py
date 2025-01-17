"""Module to handle recording of the airbrakes with a camera."""

import time
from contextlib import suppress
from multiprocessing import Event, Process

with suppress(ImportError):
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    from picamera2.outputs import CircularOutput


class Camera:
    """This is the class used to interact with the camera on our rocket. It records on a separate process."""

    __slots__ = ("camera_control_process", "motor_burn_started", "stop_cam_event")

    def __init__(self):
        self.stop_cam_event = Event()
        self.motor_burn_started = Event()
        self.camera_control_process = Process(
            target=self._camera_control_loop, name="Camera process"
        )

    def _camera_control_loop(self):
        """Starts the camera process"""
        with suppress(ImportError):
            camera = Picamera2()
            encoder = H264Encoder()
            output = CircularOutput()
            camera.configure(camera.create_video_configuration())
            camera.start_recording(encoder, output)

            while not self.motor_burn_started.is_set():
                time.sleep(0.1)

            output.fileoutput = "file.h264"
            output.start()

            while not self.stop_cam_event.is_set():
                time.sleep(0.1)

            output.stop()

    def start(self):
        """Start the video recording, with a buffer. This starts recording in a different process"""
        self.camera_control_process.start()

    def stop(self):
        """Stop the video recording."""
        self.stop_cam_event.set()
        self.camera_control_process.join()

    def start_recording(self):
        """Start recording when motor burn has started."""
        self.motor_burn_started.set()
