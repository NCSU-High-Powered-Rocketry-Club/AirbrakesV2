import math
import random

import numpy as np
import pytest

from airbrakes.data_handling.apogee_prediction import ApogeePrediction
from airbrakes.data_handling.data_processor import IMUDataProcessor
from airbrakes.data_handling.imu_data_packet import EstimatedDataPacket
from airbrakes.state import CoastState


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
    return IMUDataProcessor()


class TestIMUDataProcessor:
    """Tests the IMUDataProcessor class"""

    packets = [
        EstimatedDataPacket(1 * 1e9, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20),
        EstimatedDataPacket(2 * 1e9, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=21),
    ]

    def test_slots(self):
        inst = IMUDataProcessor()
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, np.ndarray):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, data_processor):
        d = data_processor
        assert d._max_altitude == 0.0
        assert isinstance(d._previous_velocity, np.ndarray)
        assert (d._previous_velocity == np.array([0.0, 0.0, 0.0])).all()
        assert d._initial_altitude is None
        assert isinstance(d._current_altitudes, np.ndarray)
        assert isinstance(d._speeds, np.ndarray)
        assert list(d._speeds) == [0.0]
        assert d._max_speed == 0.0
        assert d.upside_down is False
        assert d.current_altitude == 0.0
        assert list(d._current_altitudes) == [0.0]
        # See the comment in _calculate_speeds() for why speed is 0 during init.
        assert d.speed == 0.0

    def test_str(self, data_processor):
        data_str = (
            "IMUDataProcessor("
            "max_altitude=0.0, "
            "current_altitude=0.0, "
            # See the comment in _calculate_speeds() for why speed is 0 during init.
            "speed=0.0, "
            "max_speed=0.0, "
            "rotated_accel=[0. 0. 0.],)"
        )
        assert str(data_processor) == data_str

    def test_calculate_speed(self, data_processor):
        """Tests whether the speed is correctly calculated"""
        d = data_processor
        assert d.speed == 0.0
        assert d._max_speed == d.speed
        assert (d._previous_velocity == np.array([0.0, 0.0, 0.0])).all()

        d._last_data_point = EstimatedDataPacket(
            2 * 1e9, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=21
        )

        d.update(
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

        d.update(
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

        d.update(
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

    def test_first_update_no_data_packets(self, data_processor):
        """Tests whether the update() method works correctly, when no data packets are passed."""
        d = data_processor
        d.update([])
        assert d._last_data_point is None
        assert len(d._data_points) == 0
        assert len(d._current_altitudes) == 1
        assert len(d._speeds) == 1
        assert d.speed == 0.0, "Speed should be the same as set in __init__"
        assert d.current_altitude == 0.0, "Current altitude should be the same as set in __init__"
        assert d._initial_altitude is None
        assert d._max_altitude == 0.0
        assert d._last_data_point is None

    @pytest.mark.parametrize(
        (
            "data_packets",
            "init_alt",
            "max_alt",
        ),
        [
            (
                [
                    EstimatedDataPacket(
                        0 * 1e9, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20
                    )
                ],
                20.0,
                0.0,
            ),
            (
                [
                    EstimatedDataPacket(
                        1 * 1e9, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20
                    ),
                    EstimatedDataPacket(
                        2 * 1e9, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=30
                    ),
                ],
                25.0,
                5.0,
            ),
            (
                [
                    EstimatedDataPacket(
                        1 * 1e9, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=20
                    ),
                    EstimatedDataPacket(
                        2 * 1e9, estLinearAccelX=2, estLinearAccelY=3, estLinearAccelZ=4, estPressureAlt=30
                    ),
                    EstimatedDataPacket(
                        3 * 1e9, estLinearAccelX=3, estLinearAccelY=4, estLinearAccelZ=5, estPressureAlt=40
                    ),
                ],
                30.0,
                10.0,
            ),
        ],
        ids=["one_data_point", "two_data_points", "three_data_points"],
    )
    def test_first_update(self, data_processor, data_packets, init_alt, max_alt):
        """
        Tests whether the update() method works correctly, for the first update() call,
        along with get_processed_data_packets()
        """
        d = data_processor
        d.update(data_packets.copy())
        # We should always have a last data point
        assert d._last_data_point
        assert d._last_data_point == data_packets[-1]
        assert len(d._data_points) == len(data_packets)

        # the max() is there because if we only process one data packet, we just return early
        # and the variables set at __init__ are used:
        assert len(d._current_altitudes) == max(len(data_packets), 1)
        assert len(d._speeds) == max(len(data_packets), 1)
        assert len(d._speeds) == len(d._current_altitudes)
        # Our initial speed should always be zero, since we set the previous data point to the first
        # data point, giving a time difference of zero, and hence a speed of zero, and thus
        # implicitly testing it.
        assert d._speeds[0] == 0.0

        assert d._initial_altitude == init_alt
        assert d.current_altitude == (0.0 if init_alt is None else data_packets[-1].estPressureAlt - init_alt)
        assert d._max_altitude == d.max_altitude == max_alt

        processed_data = d.get_processed_data_packets()
        assert len(processed_data) == len(data_packets)
        for idx, data in enumerate(processed_data):
            assert data.current_altitude == d._current_altitudes[idx]
            assert data.speed == d._speeds[idx]

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
        data_processor.update(packets)
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
        data_processor.update(new_packets)
        second_vel = data_processor._previous_velocity

        assert second_vel[0] > first_vel[0], "Previous velocity should be updated after each data update."

    @pytest.mark.parametrize(
        # altitude reading - list of altitudes passed to the data processor (estPressureAlt)
        # current_altitude - calculated current altitude of the rocket, zeroed out.
        # max_altitude - calculated max altitude of the rocket
        ("altitude_reading", "current_altitude", "max_altitude"),
        [
            ([30, 40], 20.0, 20.0),
            ([50, 55, 60], 40.0, 40.0),
            ([30, 20, 10], -10.0, 10.0),
        ],
        ids=["increasing_altitude", "increasing_altitude_2", "negative_altitude"],
    )
    def test_altitude_zeroing(self, data_processor, altitude_reading, current_altitude, max_altitude):
        """Tests whether the altitude is correctly zeroed"""
        d = data_processor
        # test_first_update tests the initial alt update, so we can skip that here:
        d._last_data_point = EstimatedDataPacket(
            0, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=altitude_reading[0]
        )
        d._initial_altitude = 20.0

        new_packets = [
            EstimatedDataPacket(idx + 3, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=alt)
            for idx, alt in enumerate(altitude_reading)
        ]
        d.update(new_packets)
        assert d.current_altitude == current_altitude
        assert d._max_altitude == max_altitude

    def test_max_altitude(self, data_processor):
        """Tests whether the max altitude is correctly calculated even when altitude decreases"""
        d = data_processor
        altitudes = simulate_altitude_sine_wave(n_points=1000)
        # run update_data every 10 packets, to simulate actual data processing in real time:
        for i in range(0, len(altitudes), 10):
            d.update(
                [
                    EstimatedDataPacket(i, estLinearAccelX=1, estLinearAccelY=2, estLinearAccelZ=3, estPressureAlt=alt)
                    for alt in altitudes[i : i + 10]
                ]
            )
        assert d.max_altitude + d._initial_altitude == pytest.approx(max(altitudes))

    @pytest.mark.parametrize(
        ("data_packets", "expected_value"),
        [
            (
                [
                    EstimatedDataPacket(
                        timestamp=1 * 1e9,
                        estOrientQuaternionW=0.91,
                        estOrientQuaternionX=0.1,
                        estOrientQuaternionY=0.22,
                        estOrientQuaternionZ=-0.34,
                        estCompensatedAccelX=1,
                        estCompensatedAccelY=1,
                        estCompensatedAccelZ=1,
                        estLinearAccelX=0.0,
                        estLinearAccelY=0.0,
                        estLinearAccelZ=0.0,
                        estAngularRateX=0.02,
                        estAngularRateY=0.1,
                        estAngularRateZ=2,
                        estPressureAlt=0.0,
                    ),
                    EstimatedDataPacket(
                        timestamp=1.002 * 1e9,
                        estOrientQuaternionW=0.92,
                        estOrientQuaternionX=0.1,
                        estOrientQuaternionY=0.22,
                        estOrientQuaternionZ=-0.34,
                        estCompensatedAccelX=1,
                        estCompensatedAccelY=1,
                        estCompensatedAccelZ=1,
                        estLinearAccelX=0.0,
                        estLinearAccelY=0.0,
                        estLinearAccelZ=0.0,
                        estAngularRateX=0.02,
                        estAngularRateY=0.1,
                        estAngularRateZ=2,
                        estPressureAlt=0.0,
                    ),
                ],
                (1.6658015, -0.14997540, 0.450125221),
            )
        ],
    )
    def test_calculate_rotations(self, data_packets, expected_value):
        d = IMUDataProcessor([])
        d.update_data(data_packets)
        rotations = d._rotated_accel
        assert len(rotations) == 3
        for rot, expected_val in zip(rotations, expected_value, strict=False):
            assert rot == pytest.approx(expected_val)

    @pytest.mark.parametrize(
        ("data_packets", "set_state", "expected_values"),
        [
            (
                [
                    EstimatedDataPacket(
                        timestamp=1 * 1e9,
                        estOrientQuaternionW=0.91,
                        estOrientQuaternionX=0.1,
                        estOrientQuaternionY=0.22,
                        estOrientQuaternionZ=-0.34,
                        estCompensatedAccelX=1,
                        estCompensatedAccelY=1,
                        estCompensatedAccelZ=1,
                        estLinearAccelX=0.0,
                        estLinearAccelY=0.0,
                        estLinearAccelZ=0.0,
                        estAngularRateX=0.02,
                        estAngularRateY=0.1,
                        estAngularRateZ=2,
                        estPressureAlt=0.0,
                    ),
                    EstimatedDataPacket(
                        timestamp=1.002 * 1e9,
                        estOrientQuaternionW=0.92,
                        estOrientQuaternionX=0.1,
                        estOrientQuaternionY=0.22,
                        estOrientQuaternionZ=-0.34,
                        estCompensatedAccelX=1,
                        estCompensatedAccelY=1,
                        estCompensatedAccelZ=1,
                        estLinearAccelX=0.0,
                        estLinearAccelY=0.0,
                        estLinearAccelZ=0.0,
                        estAngularRateX=0.02,
                        estAngularRateY=0.1,
                        estAngularRateZ=2,
                        estPressureAlt=0.0,
                    ),
                    EstimatedDataPacket(
                        timestamp=1.002 * 1e9,
                        estOrientQuaternionW=0.92,
                        estOrientQuaternionX=0.1,
                        estOrientQuaternionY=0.22,
                        estOrientQuaternionZ=-0.34,
                        estCompensatedAccelX=1,
                        estCompensatedAccelY=1,
                        estCompensatedAccelZ=1,
                        estLinearAccelX=0.0,
                        estLinearAccelY=0.0,
                        estLinearAccelZ=0.0,
                        estAngularRateX=0.02,
                        estAngularRateY=0.1,
                        estAngularRateZ=2,
                        estPressureAlt=0.0,
                    ),
                ],
                CoastState,
                [-0.02049625, [0.45012522, 0.03], -0.00010248071212592195],
            )
        ],
    )
    def test_apogee_pred(self, data_packets, set_state, expected_values):
        d = IMUDataProcessor([])
        d.update_data([data_packets[0], data_packets[1]])
        ap_pred = ApogeePrediction(set_state, d, [])
        ap_pred.update_data([data_packets[0], data_packets[1]])
        d.update_data([data_packets[2]])
        ap_pred.update_data([data_packets[2]])

        velocity = ap_pred._speed
        assert velocity == pytest.approx(expected_values[0])

        params = ap_pred._params
        assert params == pytest.approx(expected_values[1])

        apogee_pred = ap_pred._apogee_prediction
        assert apogee_pred == pytest.approx(expected_values[2])
