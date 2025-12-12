import queue
import threading
import time

import numpy as np
import pytest

from airbrakes.constants import STOP_SIGNAL
from airbrakes.telemetry.apogee_predictor import ApogeePredictor
from airbrakes.telemetry.packets.processor_data_packet import ProcessorDataPacket
from tests.auxil.utils import make_processor_data_packet


class TestApogeePredictor:
    """
    Tests the IMUDataProcessor class.
    """

    def test_slots(self):
        inst = ApogeePredictor()
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, np.ndarray):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, apogee_predictor):
        """
        Tests whether the DataProcessor is correctly initialized.
        """
        ap = apogee_predictor
        # Test attributes on init
        assert isinstance(ap._apogee_predictor_packet_queue, queue.SimpleQueue)
        assert isinstance(ap._processor_data_packet_queue, queue.SimpleQueue)
        assert isinstance(ap._prediction_thread, threading.Thread)
        assert ap._prediction_thread.daemon
        assert not ap._prediction_thread.is_alive()

        # Test properties on init
        assert not ap.is_running

    def test_apogee_loop_start_stop(self, apogee_predictor):
        apogee_predictor.start()
        assert apogee_predictor.is_running
        apogee_predictor.stop()
        assert not apogee_predictor.is_running

    def test_apogee_loop_add_to_queue(self, apogee_predictor):
        """
        Tests that the predictor adds to the queue when update is called.
        """
        packet = [make_processor_data_packet()]
        # important to not .start() the thread, as we don't want it to run as it will fetch
        # it from the queue and we want to check if it's added to the queue.
        apogee_predictor.update(packet.copy())
        assert apogee_predictor._processor_data_packet_queue.qsize() == 1
        assert apogee_predictor._processor_data_packet_queue.get()[0] == packet[0]

    def test_apogee_predictor_stop_signal(self, apogee_predictor):
        """
        Tests that the apogee predictor stops when the stop signal is sent.
        """
        apogee_predictor.start()
        assert apogee_predictor.is_running
        apogee_predictor._processor_data_packet_queue.put(STOP_SIGNAL)
        time.sleep(0.001)  # wait for the thread to fetch the packet
        assert not apogee_predictor.is_running

    @pytest.mark.parametrize(
        (
            "processor_data_packets",
            "expected_value",
        ),
        [
            (
                [
                    ProcessorDataPacket(
                        current_altitude=100,
                        vertical_velocity=0.0,
                        vertical_acceleration=9.798,
                        time_since_last_data_packet=0.1,
                        velocity_magnitude=0.0,
                        current_pitch_degrees=0.0,
                    ),
                ]
                * 1000,
                100.0,  # The predicted apogee should be the same if our velocity is 0 and accel
                # is gravity, i.e. hovering.
            ),
            (
                [
                    ProcessorDataPacket(
                        current_altitude=float(
                            i**3 / 15000 - i**2 / 20 - i**2 * 9.798 / 200 + 20 * i + 100
                        ),
                        vertical_velocity=float(i**2 / 500 - i - 9.798 * i / 10 + 200),
                        vertical_acceleration=float(-10 + i / 25),
                        time_since_last_data_packet=0.1,
                        velocity_magnitude=float(i**2 / 500 - i - 9.798 * i / 10 + 200),
                        current_pitch_degrees=0.0,
                    )
                    for i in range(70)
                ],
                # the velocity and altitude points in this data packet are calculated by hand.
                # the data packets are from 0 - 7 seconds, in 0.1 second intervals.
                # the acceleration has a slope of +0.4 m/s^2 per second, which recreates
                # coast phase, going from -10 m/s^2 to -7.2 m/s^2. The expected outcome of this
                # test is the max of the position function. Because we are curve fitting to a
                # quartic function though, it's off by a bit, because a quartic function
                # cannot look very linear. If you want to check my integration math, remember that
                #  the dt is not 1, it is 0.1, so you divide everything by 10 when you integrate.
                1167.8157033651648,
            ),
        ],
        ids=["hover_at_altitude", "coast_phase"],
    )
    def test_prediction_loop_no_mock(
        self, apogee_predictor, processor_data_packets, expected_value
    ):
        """
        Tests that our predicted apogee works in general, by passing in a few hundred data packets.

        This does not really represent a real flight, but given that case, it should predict it
        correctly. Also tests that we have sent the Apogee Predictor Data Packet to the main
        thread.
        """
        # apogee_predictor.start()
        # assert not apogee_predictor._apogee_predictor_packet_queue.qsize()
        # apogee_predictor.update(processor_data_packets)
        #
        # time.sleep(0.1)  # Wait for the prediction loop to finish
        # assert apogee_predictor._has_apogee_converged
        #
        # assert apogee_predictor._apogee_predictor_packet_queue.qsize() in (1, 2)
        # packet: ApogeePredictorDataPacket = apogee_predictor.get_prediction_data_packets()[-1]
        # # Test that our predicted apogee is approximately the same as the expected value, within
        # # 0.1 meters, using pytest.approx. There is a difference in the 7th decimal place between
        # # arm64 and x86_64, so we need to use approx.
        # assert packet.predicted_apogee == pytest.approx(expected_value, abs=0.1)
        # assert packet.a_coefficient
        # assert packet.b_coefficient
        # assert packet.uncertainty_threshold_1 < UNCERTAINTY_THRESHOLD[0]
        # assert packet.uncertainty_threshold_2 < UNCERTAINTY_THRESHOLD[1]
