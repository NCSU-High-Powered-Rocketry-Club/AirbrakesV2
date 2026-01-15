import queue
import threading
import time

import numpy as np
import pytest

from airbrakes.constants import STOP_SIGNAL
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
from tests.auxil.utils import make_processor_data_packet


class TestApogeePredictor:
    """
    Tests the ApogeePredictor class.
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
        ("processor_data_packets", "expected_apogee"),
        [
            # Hovering case: v = 0, a ≈ g, should give apogee basically at current altitude.
            (
                [
                    ProcessorDataPacket(
                        current_altitude=100.0,
                        vertical_velocity=0.0,
                        vertical_acceleration=9.798,
                        time_since_last_data_packet=0.1,
                        velocity_magnitude=0.0,
                        current_pitch_degrees=0.0,
                    )
                ]
                * 10,
                100,
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
                1272.556161741228,
            ),
        ],
        ids=["at_apogee", "start_of_coast_phase"],
    )
    def test_prediction_loop_no_mock(
        self, apogee_predictor, processor_data_packets, expected_apogee, monkeypatch
    ):
        """
        Integration-ish test of the apogee predictor using the real HPRM call. These tests assume
        that HPRM works perfectly. To test the actual correctness of HPRM, we rely on HPRM's own
        unit tests (which will hopefully exist soon).

        - Feeds a sequence of ProcessorDataPackets into the predictor.
        - Waits for a prediction to appear on the apogee queue.
        - Asserts that:
            * A prediction was produced.
            * The height/velocity used in the prediction come from the last packet.
            * The predicted apogee matches an expected (precomputed) value.
        """
        monkeypatch.setattr("airbrakes.constants.ROCKET_DRY_MASS_KG", 4.937)
        monkeypatch.setattr("airbrakes.constants.ROCKET_CD", 0.45)
        monkeypatch.setattr("airbrakes.constants.ROCKET_CROSS_SECTIONAL_AREA_M2", 0.00810731966)
        apogee_predictor.start()

        # Feed all packets into the predictor, one by one
        for pkt in processor_data_packets:
            apogee_predictor.update(pkt)

        # Wait (with timeout) for a prediction to show up
        deadline = time.time() + 1.0  # 1 second timeout
        prediction = None
        while time.time() < deadline:
            prediction = apogee_predictor.get_prediction_data_packet()
            if prediction is not None:
                break
            time.sleep(0.01)

        # Cleanly stop the background thread
        apogee_predictor.stop()

        assert prediction is not None

        last_packet = processor_data_packets[-1]

        assert prediction.height_used_for_prediction == pytest.approx(last_packet.current_altitude)
        assert prediction.velocity_used_for_prediction == pytest.approx(
            last_packet.velocity_magnitude
        )

        assert prediction.predicted_apogee == pytest.approx(expected_apogee, rel=10e-4)
