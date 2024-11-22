import multiprocessing
import multiprocessing.queues
import threading
import time
from collections import deque

import faster_fifo
import numpy as np
import pytest

from airbrakes.data_handling.apogee_predictor import ApogeePredictor, LookupTable
from airbrakes.data_handling.processed_data_packet import ProcessedDataPacket
from constants import APOGEE_PREDICTION_FREQUENCY


@pytest.fixture
def threaded_apogee_predictor(monkeypatch):
    """Modifies the ApogeePredictor to run in a separate thread instead of a process."""
    ap = ApogeePredictor()
    # Cannot use signals from child threads, so we need to monkeypatch it:
    monkeypatch.setattr("signal.signal", lambda _, __: None)
    target = threading.Thread(target=ap._prediction_loop)
    ap._prediction_process = target
    ap.start()
    yield ap
    ap.stop()


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
        assert isinstance(ap._prediction_queue, faster_fifo.Queue)
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
        assert not ap._has_apogee_converged
        assert isinstance(ap.lookup_table, LookupTable)
        assert ap.lookup_table.velocities.size == 2
        assert ap.lookup_table.delta_heights.size == 2

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
        assert apogee_predictor._prediction_queue.get_many() == packet

    @pytest.mark.parametrize(
        (
            "processed_data_packets",
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
                100.0,  # The predicted apogee should be the same if our velocity is 0 and accel
                # is gravity, i.e. hovering.
            ),
            (
                [
                    ProcessedDataPacket(
                        current_altitude=float(
                            i**3 / 15000 - i**2 / 20 - i**2 * 9.798 / 200 + 20 * i + 100
                        ),
                        vertical_velocity=float(i**2 / 500 - i - 9.798 * i / 10 + 200),
                        vertical_acceleration=float(-10 + i / 25),
                        time_since_last_data_packet=0.1,
                    )
                    for i in range(70)
                ],
                # the velocity and altitude points in this data packet are calculated by hand.
                # the data packets simulate 0 - 7 seconds, in 0.1 second intervals.
                # the acceleration has a slope of +0.4 m/s^2 per second, which simulates
                # coast phase, going from -10 m/s^2 to -7.2 m/s^2. The expected outcome of this
                # test is the max of the position function. Because we are curve fitting to a
                # quartic function though, it's off by a bit, because a quartic function
                # cannot look very linear. If you want to check my integration math, remember that
                #  the dt is not 1, it is 0.1, so you divide everything by 10 when you integrate.
                1177.232574134796,
            ),
        ],
        ids=["hover_at_altitude", "coast_phase_sim"],
    )
    def test_prediction_loop_no_mock(
        self, threaded_apogee_predictor, processed_data_packets, expected_value
    ):
        """Tests that our predicted apogee works in general, by passing in a few hundred data
        packets. This does not really represent a real flight, but given that case, it should
        predict it correctly."""

        threaded_apogee_predictor.update(processed_data_packets)

        time.sleep(0.01)  # Wait for the prediction loop to finish
        assert threaded_apogee_predictor._has_apogee_converged
        assert threaded_apogee_predictor.apogee == expected_value

    def test_prediction_loop_every_x_packets(self, threaded_apogee_predictor):
        """Tests that the predictor only runs every APOGEE_PREDICTION_FREQUENCY packets"""

        apogees = []
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
            threaded_apogee_predictor.update(packets)
            time.sleep(0.001)  # allows update to finish
            apogees.append(threaded_apogee_predictor.apogee)

        # Assert that apogees are ascending:
        assert all(apogees[i] <= apogees[i + 1] for i in range(len(apogees) - 1))
        unique_apogees = set(apogees)
        # Assert that we have a '0' apogee in our unique apogees, and then remove that:
        # We get a 0 apogee because we don't start predicting until we have a certain amount
        # of packets.
        assert 0.0 in unique_apogees
        unique_apogees.remove(0.0)
        # amount of apogees we have is number of packets, divided by the frequency
        assert len(unique_apogees) == NUMBER_OF_PACKETS / APOGEE_PREDICTION_FREQUENCY
        assert threaded_apogee_predictor._prediction_queue.qsize() == 0
        assert threaded_apogee_predictor._has_apogee_converged
        assert threaded_apogee_predictor.apogee == max(apogees)
        assert threaded_apogee_predictor.is_running

    @pytest.mark.parametrize(
        ("cumulative_time_differences", "accelerations", "expected_convergence"),
        [
            (  # case with not enough data
                [1, 2, 3, 4],
                [1, 5, 3, 7],
                False,
            ),
            (  # valid case within the uncertainty range
                [i / 10 for i in range(20)],
                [15.5 * (1 - 0.03 * i) ** 4 for i in range(20)],
                True,
            ),
        ],
        ids=["not_enough_data", "within_30m"],
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
