import pytest

from airbrakes.data_handling.packets.apogee_predictor_data_packet import ApogeePredictorDataPacket


@pytest.fixture
def apogee_predictor_data_packet():
    return ApogeePredictorDataPacket(
        predicted_apogee=TestApogeePredictorDataPacket.predicted_apogee,
        a_coefficient=TestApogeePredictorDataPacket.a_coefficient,
        b_coefficient=TestApogeePredictorDataPacket.b_coefficient,
        uncertainty_threshold_1=TestApogeePredictorDataPacket.uncertainty_threshold_1,
        uncertainty_threshold_2=TestApogeePredictorDataPacket.uncertainty_threshold_2,
    )


class TestApogeePredictorDataPacket:
    """Tests for the ApogeePredictorPacket class."""

    predicted_apogee = 0.45
    a_coefficient = 0.5
    b_coefficient = 0.2
    uncertainty_threshold_1 = 0.1
    uncertainty_threshold_2 = 0.4

    def test_init(self, apogee_predictor_data_packet):
        packet = apogee_predictor_data_packet
        assert packet.predicted_apogee == self.predicted_apogee
        assert packet.a_coefficient == self.a_coefficient
        assert packet.b_coefficient == self.b_coefficient
        assert packet.uncertainty_threshold_1 == self.uncertainty_threshold_1
        assert packet.uncertainty_threshold_2 == self.uncertainty_threshold_2

    def test_required_args(self):
        with pytest.raises(TypeError):
            ApogeePredictorDataPacket()
