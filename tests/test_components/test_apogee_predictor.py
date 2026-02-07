import queue
import threading
import time

import numpy as np
import pytest

from airbrakes.constants import STOP_SIGNAL
from airbrakes.data_handling.apogee_predictor import ApogeePredictor
from tests.auxil.utils import make_firm_data_packet, make_firm_data_packet_zeroed


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
        Tests whether the ApogeePredictor is correctly initialized.
        """
        ap = apogee_predictor
        # Test attributes on init
        assert isinstance(ap._apogee_predictor_packet_queue, queue.SimpleQueue)
        assert isinstance(ap._firm_data_packet_queue, queue.SimpleQueue)
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
        packet = [make_firm_data_packet()]
        # important to not .start() the thread, as we don't want it to run as it will fetch
        # it from the queue and we want to check if it's added to the queue.
        apogee_predictor.update(packet.copy())
        assert apogee_predictor._firm_data_packet_queue.qsize() == 1
        assert apogee_predictor._firm_data_packet_queue.get()[0] == packet[0]

    def test_apogee_predictor_stop_signal(self, apogee_predictor):
        """
        Tests that the apogee predictor stops when the stop signal is sent.
        """
        apogee_predictor.start()
        assert apogee_predictor.is_running
        apogee_predictor._firm_data_packet_queue.put(STOP_SIGNAL)
        time.sleep(0.001)  # wait for the thread to fetch the packet
        assert not apogee_predictor.is_running

    @pytest.mark.parametrize(
        ("firm_data_packets", "expected_apogee"),
        [
            # Hovering case: v = 0, a ≈ g, should give apogee basically at current altitude.
            (
                [
                    make_firm_data_packet_zeroed(
                        est_position_z_meters=100.0, est_velocity_z_meters_per_s=0.0
                    )
                ]
                * 10,
                100,
            ),
            (
                [
                    make_firm_data_packet_zeroed(
                        est_position_z_meters=float(
                            i**3 / 15000 - i**2 / 20 - i**2 * 9.798 / 200 + 20 * i + 100
                        ),
                        est_velocity_z_meters_per_s=float(i**2 / 500 - i - 9.798 * i / 10 + 200),
                    )
                    for i in range(70)
                ],
                1272.556161741228,
            ),
        ],
        ids=["at_apogee", "start_of_coast_phase"],
    )
    def test_prediction_loop_no_mock(
        self, apogee_predictor, firm_data_packets, expected_apogee, monkeypatch
    ):
        """
        Integration-ish test of the apogee predictor using the real HPRM call. These tests assume
        that HPRM works perfectly. To test the actual correctness of HPRM, we rely on HPRM's own
        unit tests (which will hopefully exist soon).

        - Feeds a sequence of FIRMDataPackets into the predictor.
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
        for pkt in firm_data_packets:
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

        last_packet = firm_data_packets[-1]

        assert prediction.height_used_for_prediction == pytest.approx(
            last_packet.est_position_z_meters
        )
        assert prediction.velocity_used_for_prediction == pytest.approx(
            last_packet.est_velocity_z_meters_per_s
        )

        assert prediction.predicted_apogee == pytest.approx(expected_apogee, rel=10e-4)
