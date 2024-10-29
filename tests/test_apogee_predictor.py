import multiprocessing.queues
import numpy as np
import numpy.testing as npt
import pytest
from collections import deque
import multiprocessing

from airbrakes.data_handling.apogee_predictor import ApogeePredictor


@pytest.fixture
def apogee_predictor():
    return ApogeePredictor()

class TestApogeePredictor:
    """Tests the IMUDataProcessor class"""


    def test_slots(self):
        inst = ApogeePredictor()
        print(inst.__slots__)
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, np.ndarray):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"


    def test_init(self, apogee_predictor):
        """Tests whether the IMUDataProcessor is correctly initialized"""
        ap = apogee_predictor
        print(type(ap._prediction_queue))
        # Test attributes on init
        assert ap._apogee_prediction_value.value == 0.0
        assert isinstance(ap._prediction_queue, multiprocessing.queues.Queue)
        assert isinstance(ap._prediction_process, multiprocessing.Process)
        assert not ap._prediction_process.is_alive()
        assert isinstance(ap._cumulative_time_differences, np.ndarray)
        # assert ap._cumulative_time_differences.size == 0
        # assert isinstance(ap._accelerations, deque)
        # assert len(ap._accelerations) == 0
        # assert isinstance(ap._time_differences, deque)
        # assert len(ap._time_differences) == 0
        # assert isinstance(ap._current_altitude, float)
        # assert ap._current_altitude == 0.0
        # assert isinstance(ap._current_velocity, float)
        # assert ap._current_velocity == 0.0
