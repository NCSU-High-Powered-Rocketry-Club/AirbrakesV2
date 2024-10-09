import numpy
from airbrakes.state import State
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket

class ApogeePrediction:
    def __init__(self, state, data_processor, data_points):
        self.state = state
        self.data_processor = data_processor
        self.data_points = data_points

    
