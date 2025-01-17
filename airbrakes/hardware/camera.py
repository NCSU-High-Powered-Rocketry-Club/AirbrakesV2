"""Module to handle recording of the airbrakes with a camera."""


from picamera2.encoders import H264Encoder, Quality 
from picamera2 import Picamera2 

from multiprocessing import Process



class Camera:
    def __init__(self):
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_video_configuration())

        self.encoder = H264Encoder()

        self.start_camera_recording = Process(target=)

    def start(self):
        """Start the video recording. This starts recording in a different process."""

        ...
    
    def stop(self):
        """Stop the video recording."""
        ...


