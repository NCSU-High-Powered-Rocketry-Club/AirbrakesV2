import pytest

from airbrakes.telemetry.packets.apogee_predictor_data_packet import (
    ApogeePredictorDataPacket,
)


@pytest.fixture
def apogee_predictor_data_packet():
    return ApogeePredictorDataPacket(
        predicted_apogee=TestApogeePredictorDataPacket.predicted_apogee,
        height_used_for_prediction=TestApogeePredictorDataPacket.height_used_for_prediction,
        velocity_used_for_prediction=TestApogeePredictorDataPacket.velocity_used_for_prediction,
    )


class TestApogeePredictorDataPacket:
    """
    Tests for the ApogeePredictorPacket class.
    """

    predicted_apogee = 0.45
    height_used_for_prediction = 1.23
    velocity_used_for_prediction = 4.56

    def test_init(self, apogee_predictor_data_packet):
        packet = apogee_predictor_data_packet
        assert packet.predicted_apogee == self.predicted_apogee
        assert packet.height_used_for_prediction == self.height_used_for_prediction
        assert packet.velocity_used_for_prediction == self.velocity_used_for_prediction

    def test_required_args(self):
        with pytest.raises(TypeError):
            ApogeePredictorDataPacket()
