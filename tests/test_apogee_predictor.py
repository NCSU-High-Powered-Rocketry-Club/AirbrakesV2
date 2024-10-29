import multiprocessing
import multiprocessing.queues
from collections import deque

import numpy as np
import pytest

from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket


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
        assert ap._cumulative_time_differences.size == 0
        assert isinstance(ap._accelerations, deque)
        assert len(ap._accelerations) == 0
        assert isinstance(ap._time_differences, deque)
        assert len(ap._time_differences) == 0
        assert ap._current_altitude == 0.0
        assert ap._current_velocity == 0.0

        # Test properties on init
        assert ap.apogee == 0.0
        assert not ap.is_running

    def test_apogee_loop_start_stop(self, apogee_predictor):
        apogee_predictor.start()
        assert apogee_predictor.is_running
        apogee_predictor.stop()
        assert not apogee_predictor.is_running
        assert apogee_predictor._log_process.exitcode == 0

    def test_apogee_loop_add_to_queue(self,apogee_predictor):
        ap = apogee_predictor
        test_packets = [ProcessedDataPacket(
                            current_altitude=100,
                            vertical_velocity=50,
                            vertical_acceleration=-5,
                            time_since_last_data_packet=0.1,
                        ),]
        

    @pytest.mark.parametrize(
            (
                "processed_data_packets",
                "params",
                "expected_value",
            ),
            [
                (
                    [
                        ProcessedDataPacket(
                            current_altitude=100,
                            vertical_velocity=50,
                            vertical_acceleration=-5,
                            time_since_last_data_packet=0.1,
                        ),
                        ProcessedDataPacket(
                            current_altitude=105,
                            vertical_velocity=49.5,
                            vertical_acceleration=-5,
                            time_since_last_data_packet=0.1,
                        ),
                    ],
                    [15.5,0.03],
                    99999,
                ),
                (
                    [
                        ProcessedDataPacket(
                            current_altitude=100,
                            vertical_velocity=50,
                            vertical_acceleration=-5,
                            time_since_last_data_packet=0.1,
                        ),
                        ProcessedDataPacket(
                            current_altitude=105,
                            vertical_velocity=49.5,
                            vertical_acceleration=-5,
                            time_since_last_data_packet=0.1,
                        ),
                    ],
                    None,
                    0,
                ),
            ],
            ids=["realistic_params","none_params"],
    )


    def test_get_apogee(self,apogee_predictor,processed_data_packets,params,expected_value):
        """Tests the _get_apogee method for predicting apogee altitude."""

        ap = apogee_predictor
        ap.start()
        ap.update(processed_data_packets.copy())
        predicted_apogee = ap._get_apogee(params)

        # Verify result is a float and equal to predicted value
        assert isinstance(predicted_apogee, float)
        assert predicted_apogee == pytest.approx(expected_value)

