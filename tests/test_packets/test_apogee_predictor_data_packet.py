import pytest

from airbrakes.data_handling.packets.apogee_predictor_data_packet import (
    ApogeePredictorDataPacket,
)


@pytest.fixture
def apogee_predictor_data_packet():
    return ApogeePredictorDataPacket(
        predicted_apogee=TestApogeePredictorDataPacket.predicted_apogee,
        height_used_for_prediction=TestApogeePredictorDataPacket.height_used_for_prediction,
        vertical_velocity_meters_per_s_used_for_prediction=TestApogeePredictorDataPacket.vertical_velocity_meters_per_s_used_for_prediction,
        horizontal_velocity_meters_per_s_used_for_prediction=TestApogeePredictorDataPacket.horizontal_velocity_meters_per_s_used_for_prediction,
        tilt_angle_degrees_used_for_prediction=TestApogeePredictorDataPacket.tilt_angle_degrees_used_for_prediction,
        angular_rate_deg_per_s_used_for_prediction=TestApogeePredictorDataPacket.angular_rate_deg_per_s_used_for_prediction,
    )


class TestApogeePredictorDataPacket:
    """Tests for the ApogeePredictorPacket class."""

    predicted_apogee = 0.45
    height_used_for_prediction = 1.23
    vertical_velocity_meters_per_s_used_for_prediction = 4.56
    horizontal_velocity_meters_per_s_used_for_prediction = 7.89
    tilt_angle_degrees_used_for_prediction = 12.34
    angular_rate_deg_per_s_used_for_prediction = 56.78

    def test_init(self, apogee_predictor_data_packet):
        packet = apogee_predictor_data_packet
        assert packet.predicted_apogee == self.predicted_apogee
        assert packet.height_used_for_prediction == self.height_used_for_prediction
        assert packet.vertical_velocity_meters_per_s_used_for_prediction == (
            self.vertical_velocity_meters_per_s_used_for_prediction
        )
        assert packet.horizontal_velocity_meters_per_s_used_for_prediction == (
            self.horizontal_velocity_meters_per_s_used_for_prediction
        )
        assert packet.tilt_angle_degrees_used_for_prediction == (
            self.tilt_angle_degrees_used_for_prediction
        )
        assert packet.angular_rate_deg_per_s_used_for_prediction == (
            self.angular_rate_deg_per_s_used_for_prediction
        )

    def test_required_args(self):
        with pytest.raises(TypeError):
            ApogeePredictorDataPacket()
