import pytest

from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


@pytest.fixture
def servo_packet():
    return ServoDataPacket(
        set_extension="0.2",
    )


class TestServoDataPacket:
    """
    Tests for the ServoDataPacket class.
    """

    set_extension = "0.2"
    encoder_position = "1"

    def test_init(self, servo_packet):
        packet = servo_packet
        assert packet.set_extension == self.set_extension

    def test_required_args(self):
        with pytest.raises(TypeError):
            ServoDataPacket()
