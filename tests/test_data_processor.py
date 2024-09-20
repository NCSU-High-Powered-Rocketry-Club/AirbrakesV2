import math
import random

import pytest

from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket


def simulate_altitude_sine_wave(n_points=1000, frequency=0.01, amplitude=100, noise_level=3, base_altitude=20):
    """Generates a random distribution of altitudes that follow a sine wave pattern, with some
    noise added to simulate variations in the readings.

    :param n_points: The number of altitude points to generate.
    :param frequency: The frequency of the sine wave.
    :param amplitude: The amplitude of the sine wave.
    :param noise_level: The standard deviation of the Gaussian noise to add.
    :param base_altitude: The base altitude, i.e. starting altitude from sea level.
    """
    altitudes = []
    for i in range(n_points):
        # Calculate the sine wave value
        # sine wave roughly models the altitude of the rocket
        sine_value = amplitude * math.sin(math.pi * i / (n_points - 1))
        # Add Gaussian noise
        noise = random.gauss(0, noise_level)
        # Calculate the altitude at this point
        altitude_value = base_altitude + sine_value + noise
        altitudes.append(altitude_value)
    return altitudes


@pytest.fixture
def data_processor():
    # list of randomly increasing altitudes up to 1000 items
    sample_data = [
        EstimatedDataPacket(
            1, estCompensatedAccelX=1, estCompensatedAccelY=2, estCompensatedAccelZ=3, estPressureAlt=20
        )
    ]
    return IMUDataProcessor(sample_data)


class TestIMUDataProcessor:
    """Tests the IMUDataProcessor class"""

    def test_slots(self, data_processor):
        inst = data_processor
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, data_processor):
        d = IMUDataProcessor([])
        assert d._avg_accel == (0.0, 0.0, 0.0)
        assert d._avg_accel_mag == 0.0
        assert d._max_altitude == 0.0

        d = data_processor
        assert d._avg_accel == (1, 2, 3)
        assert d._avg_accel_mag == math.sqrt(1**2 + 2**2 + 3**2)
        assert d._max_altitude == 20

    def test_str(self, data_processor):
        assert (
            str(data_processor) == "IMUDataProcessor(avg_acceleration=(1.0, 2.0, 3.0), "
            "avg_acceleration_mag=3.7416573867739413, max_altitude=20)"
        )

    def test_update_data(self, data_processor):
        d = data_processor
        d.update_data(
            [
                EstimatedDataPacket(
                    1, estCompensatedAccelX=1, estCompensatedAccelY=2, estCompensatedAccelZ=3, estPressureAlt=20
                ),
                EstimatedDataPacket(
                    2, estCompensatedAccelX=2, estCompensatedAccelY=3, estCompensatedAccelZ=4, estPressureAlt=30
                ),
            ]
        )
        assert d._avg_accel == (1.5, 2.5, 3.5) == d.avg_acceleration
        assert d._avg_accel_mag == math.sqrt(1.5**2 + 2.5**2 + 3.5**2) == d.avg_acceleration_mag
        assert d.avg_acceleration_z == 3.5
        assert d._max_altitude == 30 == d.max_altitude

    def test_max_altitude(self, data_processor):
        """Tests whether the max altitude is correctly calculated even when alititude decreases"""
        d = data_processor
        altitudes = simulate_altitude_sine_wave(n_points=1000)
        # run update_data every 10 packets, to simulate actual data processing in real time:
        for i in range(0, len(altitudes), 10):
            d.update_data(
                [
                    EstimatedDataPacket(
                        i, estCompensatedAccelX=1, estCompensatedAccelY=2, estCompensatedAccelZ=3, estPressureAlt=alt
                    )
                    for alt in altitudes[i : i + 10]
                ]
            )
        assert d.max_altitude == max(altitudes)
