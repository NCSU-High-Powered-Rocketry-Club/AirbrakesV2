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
    return IMUDataProcessor(TestIMUDataProcessor.packets)


class TestIMUDataProcessor:
    """Tests the IMUDataProcessor class"""

    packets = [
        EstimatedDataPacket(1, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20),
        EstimatedDataPacket(2, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=21),
    ]

    def test_slots(self, data_processor):
        inst = data_processor
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, data_processor):
        d = IMUDataProcessor([])
        assert d._avg_accel == (0.0, 0.0, 0.0)
        assert d._avg_accel_mag == 0.0
        assert d._max_altitude == 0.0
        assert d._previous_velocity == (0.0, 0.0, 0.0)
        assert d._zeroed_altitude is None
        assert d._current_altitude is None
        assert d._data_points == []
        assert d._speed == 0.0
        assert d._max_speed == 0.0
        assert d.upside_down is False

        d = data_processor
        assert d._avg_accel == (1.5, 2.5, 3.5)
        assert d._avg_accel_mag == math.sqrt(1.5**2 + 2.5**2 + 3.5**2)
        assert d._max_altitude == 0.5
        assert d._current_altitude == 0.5
        assert d._zeroed_altitude == 20.5
        assert isinstance(d._speed, float)
        assert d._speed == math.sqrt(1**2 + 2**2 + 3**2)
        assert d._max_speed == d._speed
        assert d._previous_velocity == (1, 2, 3)
        assert d.upside_down is False

    def test_str(self, data_processor):
        data_processor._avg_accel = tuple(float(i) for i in data_processor.avg_acceleration)
        data_str = (
            "IMUDataProcessor("
            f"avg_acceleration=(1.5, 2.5, 3.5), "
            f"avg_acceleration_mag={math.sqrt(1.5**2 + 2.5**2 + 3.5**2)}, "
            "max_altitude=0.5, "
            "current_altitude=0.5, "
            f"speed={math.sqrt(1**2 + 2**2 + 3**2)}, "
            f"max_speed={math.sqrt(1**2 + 2**2 + 3**2)})"
        )
        assert str(data_processor) == data_str

    def test_calculate_speed(self, data_processor):
        """Tests whether the speed is correctly calculated"""
        d = data_processor
        assert d._speed == math.sqrt(1**2 + 2**2 + 3**2)
        assert d._max_speed == d._speed
        assert d._previous_velocity == (1, 2, 3)

        d.update_data(
            [
                EstimatedDataPacket(2.1, estLinearAccelX=3, estLinearAccelY=4, estLinearAccelZ=5, estPressureAlt=22),
                EstimatedDataPacket(2.2, estLinearAccelX=4, estLinearAccelY=5, estLinearAccelZ=6, estPressureAlt=23),
            ]
        )
        # we use pytest.approx() because of floating point errors
        assert d._previous_velocity == pytest.approx((1.3, 2.4, 3.5))
        assert d._speed == math.sqrt(1.3**2 + 2.4**2 + 3.5**2)
        assert d._max_speed == d._speed

        d.update_data(
            [
                EstimatedDataPacket(2.3, estLinearAccelX=5, estLinearAccelY=6, estLinearAccelZ=7, estPressureAlt=24),
                EstimatedDataPacket(2.4, estLinearAccelX=6, estLinearAccelY=7, estLinearAccelZ=8, estPressureAlt=25),
                EstimatedDataPacket(2.5, estLinearAccelX=7, estLinearAccelY=8, estLinearAccelZ=9, estPressureAlt=26),
            ]
        )
        assert d._previous_velocity == pytest.approx((2.4, 3.7, 5.0))
        assert d._speed == pytest.approx(math.sqrt(2.4**2 + 3.7**2 + 5.0**2))
        assert d._max_speed == d._speed

        d.update_data(
            [
                EstimatedDataPacket(2.6, estLinearAccelX=2, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=27),
                EstimatedDataPacket(2.7, estLinearAccelX=1, estLinearAccelY=-2, estLinearAccelZ=-1, estPressureAlt=28),
                EstimatedDataPacket(2.8, estLinearAccelX=-1, estLinearAccelY=-4, estLinearAccelZ=-5, estPressureAlt=29),
                EstimatedDataPacket(2.9, estLinearAccelX=-1, estLinearAccelY=-1, estLinearAccelZ=-1, estPressureAlt=30),
            ]
        )

        assert d._previous_velocity == pytest.approx((2.6, 3.3, 4.7))
        assert d._speed == pytest.approx(math.sqrt(2.6**2 + 3.3**2 + 4.7**2))
        assert d._max_speed != d._speed
        assert d._max_speed == pytest.approx(math.sqrt(2.4**2 + 3.7**2 + 5.0**2))

    def test_update_data(self, data_processor):
        d = data_processor
        data_points = [
            EstimatedDataPacket(1, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20),
            EstimatedDataPacket(2, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=30),
        ]
        d.update_data(data_points)
        assert d._avg_accel == (1.5, 2.5, 3.5) == d.avg_acceleration
        assert d._avg_accel_mag == math.sqrt(1.5**2 + 2.5**2 + 3.5**2) == d.avg_acceleration_mag
        assert d.avg_acceleration_z == 3.5
        assert d._max_altitude == 9.5 == d.max_altitude == d.current_altitude
        assert d._data_points == data_points
        assert d._zeroed_altitude == 20.5
        assert d.speed == math.sqrt(2**2 + 4**2 + 6**2) == d.max_speed

    @pytest.mark.parametrize(
        # altitude reading - list of altitudes passed to the data processor (estPressureAlt)
        # current_altitude - calculated current altitude of the rocket, zeroed out.
        # max_altitude - calculated max altitude of the rocket
        ("altitude_reading", "current_altitude", "max_altitude"),
        [
            ([30, 40], 19.5, 19.5),
            ([50, 55, 60], 39.5, 39.5),
            ([20, 10], -10.5, 0.5),
        ],
        ids=["increasing_altitude", "increasing_altitude_2", "negative_altitude"],
    )
    def test_altitude_zeroing(self, data_processor, altitude_reading, current_altitude, max_altitude):
        """Tests whether the altitude is correctly zeroed"""
        d = data_processor
        assert d._zeroed_altitude == 20.5
        assert d._current_altitude == 0.5
        assert d._max_altitude == 0.5

        new_packets = [
            EstimatedDataPacket(idx + 3, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=alt)
            for idx, alt in enumerate(altitude_reading)
        ]
        d.update_data(new_packets)
        assert d._zeroed_altitude == 20.5
        assert d._current_altitude == d.current_altitude == current_altitude
        assert d._max_altitude == max_altitude

    def test_max_altitude(self, data_processor):
        """Tests whether the max altitude is correctly calculated even when altitude decreases"""
        d = data_processor
        altitudes = simulate_altitude_sine_wave(n_points=1000)
        # run update_data every 10 packets, to simulate actual data processing in real time:
        for i in range(0, len(altitudes), 10):
            d.update_data(
                [
                    EstimatedDataPacket(i, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=alt)
                    for alt in altitudes[i : i + 10]
                ]
            )
        assert d.max_altitude + d._zeroed_altitude == max(altitudes)
