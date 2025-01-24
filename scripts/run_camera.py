from picamera2.encoders import H264Encoder
from picamera2 import Picamera2 

from picamera2.outputs import CircularOutput
import time


camera = Picamera2()
# We use the H264 encoder and a circular output to save the video to a file.
encoder = H264Encoder()
# The circular output is a buffer with a default size of 150 bytes? which according to
# the docs is enough for 5 seconds of video at 30 fps.
output = CircularOutput()
# Create a basic video configuration
config = camera.create_video_configuration()
camera.configure(config)

# Start recording with the buffer. This operation is non-blocking.
camera.start_recording(encoder, output)

output.fileoutput = "test.h264"
output.start()
print("not blocking")

time.sleep(10)

output.stop()
