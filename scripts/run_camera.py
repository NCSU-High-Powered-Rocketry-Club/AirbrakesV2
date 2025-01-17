from picamera2.encoders import H264Encoder, Quality 
from picamera2 import Picamera2 
import time


picam2 = Picamera2()

picam2.configure(picam2.create_video_configuration())

encoder = H264Encoder()

picam2.start_recording(encoder, 'test.h264', quality=Quality.HIGH)
print("not blocking")

time.sleep(10)

picam2.stop_recording()