import math
import random

import numpy as np
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
        EstimatedDataPacket(1 * 1e9, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20),
        EstimatedDataPacket(2 * 1e9, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=21),
    ]

    def test_slots(self):
        inst = IMUDataProcessor([])
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, np.ndarray):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, data_processor):
        d = IMUDataProcessor([])
        assert d._max_altitude == 0.0
        assert isinstance(d._previous_velocity, np.ndarray)
        assert (d._previous_velocity == np.array([0.0, 0.0, 0.0])).all()
        assert d._initial_altitude is None
        assert isinstance(d._current_altitudes, np.ndarray)
        assert d._current_altitudes == [0.0]
        assert d._data_points == []
        assert isinstance(d._speeds, list)
        assert d._speeds == [0.0]
        assert d._max_speed == 0.0
        assert d.upside_down is False

        d = data_processor
        assert d._max_altitude == 0.5
        assert d.current_altitude == 0.5
        assert list(d._current_altitudes) == [-0.5, 0.5]
        assert d._initial_altitude == 20.5
        assert isinstance(d.speed, float)
        # See the comment in _calculate_speeds() for why speed is 0 during init.
        assert d.speed == 0.0
        assert d._max_speed == d.speed
        assert (d._previous_velocity == np.array([0.0, 0.0, 0.0])).all()
        assert d.upside_down is False

    def test_str(self, data_processor):
        data_str = (
            "IMUDataProcessor("
            "max_altitude=0.5, "
            "current_altitude=0.5, "
            # See the comment in _calculate_speeds() for why speed is 0 during init.
            "speed=0.0, "
            "max_speed=0.0)"
        )
        assert str(data_processor) == data_str

    def test_calculate_speed(self, data_processor):
        """Tests whether the speed is correctly calculated"""
        d = data_processor
        assert d.speed == 0.0
        assert d._max_speed == d.speed
        assert (d._previous_velocity == np.array([0.0, 0.0, 0.0])).all()
        assert d._last_data_point == d._data_points[-1]

        d.update_data(
            [
                EstimatedDataPacket(
                    3 * 1e9, estLinearAccelX=3, estLinearAccelY=4, estLinearAccelZ=5, estPressureAlt=22
                ),
                EstimatedDataPacket(
                    4 * 1e9, estLinearAccelX=4, estLinearAccelY=5, estLinearAccelZ=6, estPressureAlt=23
                ),
            ]
        )
        # we use pytest.approx() because of floating point errors
        assert d._previous_velocity == pytest.approx((7.0, 9.0, 11.0))
        assert d.speed == math.sqrt(7.0**2 + 9.0**2 + 11.0**2)
        assert len(d._speeds) == 2
        assert d._max_speed == d.speed

        d.update_data(
            [
                EstimatedDataPacket(
                    5 * 1e9, estLinearAccelX=5, estLinearAccelY=6, estLinearAccelZ=7, estPressureAlt=24
                ),
                EstimatedDataPacket(
                    6 * 1e9, estLinearAccelX=6, estLinearAccelY=7, estLinearAccelZ=8, estPressureAlt=25
                ),
                EstimatedDataPacket(
                    7 * 1e9, estLinearAccelX=7, estLinearAccelY=8, estLinearAccelZ=9, estPressureAlt=26
                ),
            ]
        )
        assert d._previous_velocity == pytest.approx((25.0, 30.0, 35.0))
        assert d.speed == pytest.approx(math.sqrt(25.0**2 + 30.0**2 + 35.0**2))
        assert len(d._speeds) == 3
        assert d._max_speed == d.speed

        d.update_data(
            [
                EstimatedDataPacket(
                    8 * 1e9, estLinearAccelX=2, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=27
                ),
                EstimatedDataPacket(
                    9 * 1e9, estLinearAccelX=1, estLinearAccelY=-2, estLinearAccelZ=-1, estPressureAlt=28
                ),
                EstimatedDataPacket(
                    10 * 1e9, estLinearAccelX=-1, estLinearAccelY=-4, estLinearAccelZ=-5, estPressureAlt=29
                ),
                EstimatedDataPacket(
                    11 * 1e9, estLinearAccelX=-1, estLinearAccelY=-1, estLinearAccelZ=-1, estPressureAlt=30
                ),
            ]
        )

        assert d._previous_velocity == pytest.approx((26.0, 25.0, 31.0))
        assert d.speed == pytest.approx(math.sqrt(26.0**2 + 25.0**2 + 31.0**2))
        assert d._max_speed != d.speed
        # Our max speed is hit with the first est data packet on this update:
        assert d._max_speed == pytest.approx(math.sqrt(27.0**2 + 32.0**2 + 38.0**2))

    def test_update_data(self, data_processor):
        d = data_processor
        data_points = [
            EstimatedDataPacket(1 * 1e9, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20),
            EstimatedDataPacket(2 * 1e9, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=30),
        ]
        d.update_data(data_points)
        assert d._data_points == data_points
        assert len(d._current_altitudes) == 2
        assert len(d._speeds) == 2
        assert len(d._data_points) == 2
        assert d._max_altitude == 9.5 == d.max_altitude == d.current_altitude
        assert d._initial_altitude == 20.5
        assert d._last_data_point == data_points[-1]
        # Speed calculation will be updated after kalman filter
        # assert d.speed == pytest.approx(np.sqrt(2**2 + 4**2 + 6**2)) == d.max_speed

    def test_calculate_speeds_no_data(self):
        """Test that speeds are not handled when there are no data points."""
        d = IMUDataProcessor([])
        speeds = d._calculate_speeds([], [], [])
        assert speeds == [0.0], "Speeds should return [0.0] when no data points are present."

    def test_previous_velocity_retained(self, data_processor):
        """Test that previous velocity is retained correctly between updates."""
        # Initial data packet
        x_accel = [1, 2, 3]
        y_accel = [0, 0, 0]
        z_accel = [0, 0, 0]

        packets = [
            EstimatedDataPacket(
                1.0 * 1e9,
                estLinearAccelX=x_accel[0],
                estLinearAccelY=y_accel[0],
                estLinearAccelZ=z_accel[0],
                estPressureAlt=0,
            ),
            EstimatedDataPacket(
                2.0 * 1e9,
                estLinearAccelX=x_accel[1],
                estLinearAccelY=y_accel[1],
                estLinearAccelZ=z_accel[1],
                estPressureAlt=0,
            ),
        ]
        data_processor.update_data(packets)
        first_vel = data_processor._previous_velocity

        # Additional data packet
        new_packets = [
            EstimatedDataPacket(
                3.0 * 1e9,
                estLinearAccelX=x_accel[2],
                estLinearAccelY=y_accel[2],
                estLinearAccelZ=z_accel[2],
                estPressureAlt=0,
            ),
        ]
        data_processor.update_data(new_packets)
        second_vel = data_processor._previous_velocity

        assert second_vel[0] > first_vel[0], "Previous velocity should be updated after each data update."

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
        assert d._initial_altitude == 20.5
        assert d.current_altitude == 0.5
        assert d._current_altitudes[-1] == 0.5
        assert d._max_altitude == 0.5

        new_packets = [
            EstimatedDataPacket(idx + 3, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=alt)
            for idx, alt in enumerate(altitude_reading)
        ]
        d.update_data(new_packets)
        assert d._initial_altitude == 20.5
        assert d.current_altitude == current_altitude
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
        assert d.max_altitude + d._initial_altitude == max(altitudes)
