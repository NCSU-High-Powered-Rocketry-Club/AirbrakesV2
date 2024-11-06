import multiprocessing
import multiprocessing.queues
import time
from collections import deque

import numpy as np
import pytest

from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import APOGEE_PREDICTION_FREQUENCY, MIN_PREDICTION_TIME


@pytest.fixture
def apogee_predictor():
    return ApogeePredictor()


class TestApogeePredictor:
    """Tests the IMUDataProcessor class"""

    def test_slots(self):
        inst = ApogeePredictor()
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, np.ndarray):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, apogee_predictor):
        """Tests whether the IMUDataProcessor is correctly initialized"""
        ap = apogee_predictor
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
        assert ap._current_altitude == np.float64(0.0)
        assert ap._current_velocity == np.float64(0.0)

        # Test properties on init
        assert ap.apogee == 0.0
        assert not ap.is_running

    def test_apogee_loop_start_stop(self, apogee_predictor):
        apogee_predictor.start()
        assert apogee_predictor.is_running
        apogee_predictor.stop()
        assert not apogee_predictor.is_running
        assert apogee_predictor._prediction_process.exitcode == 0

    def test_apogee_loop_add_to_queue(self, apogee_predictor):
        """Tests that the predictor adds to the queue when update is called"""
        packet = [
            ProcessedDataPacket(
                current_altitude=100,
                vertical_velocity=50,
                vertical_acceleration=-5,
                time_since_last_data_packet=0.1,
            )
        ]
        # important to not .start() the process, as we don't want it to run as it will fetch
        # it from the queue and we want to check if it's added to the queue.
        apogee_predictor.update(packet.copy())
        assert apogee_predictor._prediction_queue.qsize() == 1
        assert apogee_predictor._prediction_queue.get() == packet

    @pytest.mark.parametrize(
        (
            "processed_data_packets",
            "update_packet",
            "expected_value",
        ),
        [
            (
                [
                    ProcessedDataPacket(
                        current_altitude=100,
                        vertical_velocity=0.0,
                        vertical_acceleration=9.798,
                        time_since_last_data_packet=0.1,
                    ),
                ]
                * 100,
                [
                    ProcessedDataPacket(
                        current_altitude=100,
                        vertical_velocity=0.0,
                        vertical_acceleration=9.798,
                        time_since_last_data_packet=0.1,
                    )
                ],
                100.0,  # The predicted apogee should be the same if our velocity is 0 and accel
                # is gravity, i.e. hovering.
            ),
            # TODO: Fix this test case. This test case is wrong as the acceleration doesn't change
            #  this makes it essentially the same as the previous test case.
            # (
            #     [
            #         ProcessedDataPacket(
            #             current_altitude=float(100 + (alt * 5)),  # Goes up to 595m
            #             vertical_velocity=50,
            #             vertical_acceleration=9.798,
            #             time_since_last_data_packet=0.1,
            #         )
            #         for alt in range(100)
            #     ],
            #     1600,  # After 30 seconds, the length of estAccel is 300 (30/0.1 = 300)
            #     # But length of est_vel is 200, i.e. 20 seconds. So estimated apogee should
            #     # be: 600 + (200 * (50 m/s /10)) = 1600
            # ),
        ],
        ids=["hover_at_altitude"],  # , "constant_alt_increase"],
    )
    def test_prediction_loop_no_mock(
        self, apogee_predictor, processed_data_packets, update_packet, expected_value
    ):
        """Tests that our predicted apogee works in general, by passing in a few hundred data
        packets. This does not really represent a real flight, but given that case, it should
        predict it correctly."""

        ap = apogee_predictor
        ap.start()

        ap.update(processed_data_packets.copy())
        # waits small time for process to complete
        time.sleep(0.1)

        # I have no clue how to check values from ap. After calling ap.update(), printing
        # ap._accelerations or any other similar .self variable returns default init value.

        ap.update(update_packet.copy())
        time.sleep(0.01)


        predicted_apogee = ap.apogee
        # Verify result is a float and equal to predicted value
        assert isinstance(predicted_apogee, float)
        assert predicted_apogee == pytest.approx(expected_value)

    def test_prediction_loop_every_x_packets(self, apogee_predictor):
        """Tests that the predictor only runs every APOGEE_PREDICTION_FREQUENCY packets"""
        ap = apogee_predictor
        apogees = []
        ap.start()
        NUMBER_OF_PACKETS = 300
        for i in range(NUMBER_OF_PACKETS):
            packets = [
                ProcessedDataPacket(
                    current_altitude=100 + i,  # add random alt so our prediction is different
                    vertical_velocity=2.0 + i,
                    vertical_acceleration=10.798,
                    time_since_last_data_packet=0.01,
                )
            ]
            ap.update(packets.copy())

            # allows update to finish
            time.sleep(0.001)
            apogees.append(ap.apogee)
        # sleep a bit again so the last prediction can finish:
        time.sleep(0.01)
        apogees.append(ap.apogee)
        unique_apogees = set(apogees)
        # Assert that we have a '0' apogee in our unique apogees, and then remove that:
        # We get a 0 apogee because we don't start predicting until we have 100 packets.
        assert 0.0 in unique_apogees
        unique_apogees.remove(0.0)
        # 3 different apogees, one for each 100 packets.
        assert len(unique_apogees) == NUMBER_OF_PACKETS / APOGEE_PREDICTION_FREQUENCY
        assert ap._prediction_queue.qsize() == 0
        ap.stop()

    @pytest.mark.parametrize(
        ("cumulative_time_differences", "accelerations", "expected_convergence"),
        [
            ([],[], False), # case with no data

            ( # case with not enough data
                [1] * int(np.ceil(MIN_PREDICTION_TIME * APOGEE_PREDICTION_FREQUENCY) - 1),
                [1] * int(np.ceil(MIN_PREDICTION_TIME * APOGEE_PREDICTION_FREQUENCY) - 1),
                False,
                ),

            ( # valid case within the uncertainty range
                [],
                [],
                True,
            ),
        ],
        ids=["no_data","not_enough_data","within_30m"]
    )
    def test_has_apogee_converged(
        self,
        apogee_predictor,
        cumulative_time_differences,
        accelerations,
        expected_convergence,
        ):
        """
        Test _has_apogee_converged with different lists of predicted apogees and expected results.
        """
        # Set up the apogee predictor with the test data
        ap = apogee_predictor
        ap._cumulative_time_differences = cumulative_time_differences
        ap._accelerations = accelerations
        ap._curve_fit()

        # Check if the convergence result matches the expected value

        assert apogee_predictor._has_apogee_converged == expected_convergence
