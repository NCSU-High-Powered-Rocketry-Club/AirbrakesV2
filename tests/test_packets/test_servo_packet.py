import pytest

from airbrakes.data_handling.packets.servo_data_packet import ServoDataPacket


@pytest.fixture
def servo_packet():
    return ServoDataPacket(
        current_position=0.5,
        current_temp=25.0,
        voltage=3.7,
        system_current_milliamps=500.0,
        battery_volts=3.7
    )

class TestServoDataPacket:
    """Tests for the ServoDataPacket class."""

    def test_init(self, servo_packet):
        packet = servo_packet
        assert packet.current_position == 0.5
        assert packet.current_temp == 25.0
        assert packet.voltage == 3.7
        assert packet.system_current_milliamps == 500.0
        assert packet.battery_volts == 3.7

    def test_required_args(self):
        with pytest.raises(TypeError):
            ServoDataPacket(current_position=0.5,
                            current_temp=25.0,
                            voltage=3.7,
                            system_current_milliamps=500.0)
