import math
import random

import numpy as np
import numpy.testing as npt
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
    return IMUDataProcessor()


class TestIMUDataProcessor:
    """Tests the IMUDataProcessor class"""

    packets = [
        EstimatedDataPacket(
            1 * 1e9,
            estLinearAccelX=1,
            estLinearAccelY=2,
            estLinearAccelZ=3,
            estPressureAlt=20,
            estOrientQuaternionW=0.1,
            estOrientQuaternionX=0.2,
            estOrientQuaternionY=0.3,
            estOrientQuaternionZ=0.4,
            estGravityVectorX=0,
            estGravityVectorY=0,
            estGravityVectorZ=9.8,
        ),
        EstimatedDataPacket(
            2 * 1e9,
            estLinearAccelX=2,
            estLinearAccelY=3,
            estLinearAccelZ=4,
            estPressureAlt=21,
            estOrientQuaternionW=0.1,
            estOrientQuaternionX=0.2,
            estOrientQuaternionY=0.3,
            estOrientQuaternionZ=0.4,
            estGravityVectorX=0,
            estGravityVectorY=0,
            estGravityVectorZ=9.8,
        ),
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
        assert isinstance(d._previous_vertical_velocity, np.float64)
        assert d._previous_vertical_velocity == 0.0
        assert d._initial_altitude is None
        assert isinstance(d._current_altitudes, np.ndarray)
        assert isinstance(d._vertical_velocities, np.ndarray)
        assert list(d._vertical_velocities) == [0.0]
        assert d._max_vertical_velocity == 0.0
        assert d.current_altitude == 0.0
        assert list(d._current_altitudes) == [0.0]
        # See the comment in _calculate_velocitys() for why velocity is 0 during init.
        assert d.vertical_velocity == 0.0

    def test_str(self, data_processor):
        data_str = "IMUDataProcessor(max_altitude=0.0, current_altitude=0.0, velocity=0.0, " "max_velocity=0.0, "
        assert str(data_processor) == data_str

    def test_calculate_velocity(self, data_processor):
        """Tests whether the velocity is correctly calculated"""
        d = data_processor
        assert d.vertical_velocity == 0.0
        assert d._max_vertical_velocity == d.vertical_velocity
        assert d._previous_vertical_velocity == 0

        d.update(
            [
                EstimatedDataPacket(
                    2 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=10,
                    estPressureAlt=21,
                    estOrientQuaternionW=0.08,
                    estOrientQuaternionX=0.0,
                    estOrientQuaternionY=0.0,
                    estOrientQuaternionZ=-0.5,
                    estGravityVectorX=0,
                    estGravityVectorY=0,
                    estGravityVectorZ=-9.8,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
                EstimatedDataPacket(
                    3 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=15,
                    estPressureAlt=22,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
                EstimatedDataPacket(
                    4 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=20,
                    estPressureAlt=23,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
            ]
        )
        # we use pytest.approx() because of floating point errors
        assert d._previous_vertical_velocity == pytest.approx(15.38026)
        assert len(d._vertical_velocities) == 3
        assert d._max_vertical_velocity == d.vertical_velocity

        # This tests that we are now falling (the accel is less than 9.8)
        d.update(
            [
                EstimatedDataPacket(
                    5 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=30,
                    estPressureAlt=24,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
                EstimatedDataPacket(
                    6 * 1e9,
                    estCompensatedAccelX=6,
                    estCompensatedAccelY=7,
                    estCompensatedAccelZ=8,
                    estPressureAlt=25,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
                EstimatedDataPacket(
                    7 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=5,
                    estPressureAlt=26,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
            ]
        )
        assert d._previous_vertical_velocity == pytest.approx(28.70443)
        assert d.vertical_velocity == pytest.approx(28.70443)
        assert len(d._vertical_velocities) == 3
        # It's falling now so the max velocity should greater than the current velocity
        assert d._max_vertical_velocity != d.vertical_velocity

    def test_first_update_no_data_packets(self, data_processor):
        """Tests whether the update() method works correctly, when no data packets are passed."""
        d = data_processor
        d.update([])
        assert d._last_data_packet is None
        assert len(d._data_packets) == 0
        assert len(d._current_altitudes) == 1
        assert len(d._vertical_velocities) == 1
        assert d.vertical_velocity == 0.0, "velocity should be the same as set in __init__"
        assert d.current_altitude == 0.0, "Current altitude should be the same as set in __init__"
        assert d._initial_altitude is None
        assert d._max_altitude == 0.0
        assert d._last_data_packet is None

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
                        0 * 1e9,
                        estLinearAccelX=1,
                        estLinearAccelY=2,
                        estLinearAccelZ=3,
                        estPressureAlt=20,
                        estOrientQuaternionW=0.1,
                        estOrientQuaternionX=0.2,
                        estOrientQuaternionY=0.3,
                        estOrientQuaternionZ=0.4,
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=9.8,
                    )
                ],
                20.0,
                0.0,
            ),
            (
                [
                    EstimatedDataPacket(
                        1 * 1e9,
                        estLinearAccelX=1,
                        estLinearAccelY=2,
                        estLinearAccelZ=3,
                        estPressureAlt=20,
                        estOrientQuaternionW=0.1,
                        estOrientQuaternionX=0.2,
                        estOrientQuaternionY=0.3,
                        estOrientQuaternionZ=0.4,
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=9.8,
                    ),
                    EstimatedDataPacket(
                        2 * 1e9,
                        estLinearAccelX=2,
                        estLinearAccelY=3,
                        estLinearAccelZ=4,
                        estPressureAlt=30,
                        estOrientQuaternionW=0.1,
                        estOrientQuaternionX=0.2,
                        estOrientQuaternionY=0.3,
                        estOrientQuaternionZ=0.4,
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=9.8,
                    ),
                ],
                25.0,
                5.0,
            ),
            (
                [
                    EstimatedDataPacket(
                        1 * 1e9,
                        estLinearAccelX=1,
                        estLinearAccelY=2,
                        estLinearAccelZ=3,
                        estPressureAlt=20,
                        estOrientQuaternionW=0.1,
                        estOrientQuaternionX=0.2,
                        estOrientQuaternionY=0.3,
                        estOrientQuaternionZ=0.4,
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=9.8,
                    ),
                    EstimatedDataPacket(
                        2 * 1e9,
                        estLinearAccelX=2,
                        estLinearAccelY=3,
                        estLinearAccelZ=4,
                        estPressureAlt=30,
                        estOrientQuaternionW=0.1,
                        estOrientQuaternionX=0.2,
                        estOrientQuaternionY=0.3,
                        estOrientQuaternionZ=0.4,
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=9.8,
                    ),
                    EstimatedDataPacket(
                        3 * 1e9,
                        estLinearAccelX=3,
                        estLinearAccelY=4,
                        estLinearAccelZ=5,
                        estPressureAlt=40,
                        estOrientQuaternionW=0.1,
                        estOrientQuaternionX=0.2,
                        estOrientQuaternionY=0.3,
                        estOrientQuaternionZ=0.4,
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=9.8,
                    ),
                ],
                30.0,
                10.0,
            ),
        ],
        ids=["one_data_packet", "two_data_packets", "three_data_packets"],
    )
    def test_first_update(self, data_processor, data_packets, init_alt, max_alt):
        """
        Tests whether the update() method works correctly, for the first update() call,
        along with get_processed_data_packets()
        """
        d = data_processor
        d.update(data_packets.copy())
        # We should always have a last data point
        assert d._last_data_packet
        assert d._last_data_packet == data_packets[-1]
        assert len(d._data_packets) == len(data_packets)

        # the max() is there because if we only process one data packet, we just return early
        # and the variables set at __init__ are used:
        assert len(d._current_altitudes) == max(len(data_packets), 1)
        assert len(d._vertical_velocities) == max(len(data_packets), 1)
        assert len(d._vertical_velocities) == len(d._current_altitudes)
        # Our initial velocity should always be zero, since we set the previous data point to the first
        # data point, giving a time difference of zero, and hence a velocity of zero, and thus
        # implicitly testing it.
        assert d._vertical_velocities[0] == 0.0

        assert d._initial_altitude == init_alt
        assert d.current_altitude == (0.0 if init_alt is None else data_packets[-1].estPressureAlt - init_alt)
        assert d._max_altitude == d.max_altitude == max_alt

        processed_data = d.get_processed_data_packets()
        assert len(processed_data) == len(data_packets)
        for idx, data in enumerate(processed_data):
            assert data.current_altitude == d._current_altitudes[idx]
            assert data.vertical_velocity == d._vertical_velocities[idx]

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
        d._last_data_packet = EstimatedDataPacket(
            0,
            estLinearAccelX=1,
            estLinearAccelY=2,
            estLinearAccelZ=3,
            estPressureAlt=altitude_reading[0],
            estOrientQuaternionW=0.1,
            estOrientQuaternionX=0.2,
            estOrientQuaternionY=0.3,
            estOrientQuaternionZ=0.4,
            estGravityVectorX=0,
            estGravityVectorY=0,
            estGravityVectorZ=9.8,
        )
        d._initial_altitude = 20.0

        new_packets = [
            EstimatedDataPacket(
                idx + 3,
                estLinearAccelX=1,
                estLinearAccelY=2,
                estLinearAccelZ=3,
                estPressureAlt=alt,
                estOrientQuaternionW=0.1,
                estOrientQuaternionX=0.2,
                estOrientQuaternionY=0.3,
                estOrientQuaternionZ=0.4,
                estGravityVectorX=0,
                estGravityVectorY=0,
                estGravityVectorZ=9.8,
            )
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
                    EstimatedDataPacket(
                        i,
                        estLinearAccelX=1,
                        estLinearAccelY=2,
                        estLinearAccelZ=3,
                        estPressureAlt=alt,
                        estOrientQuaternionW=0.1,
                        estOrientQuaternionX=0.2,
                        estOrientQuaternionY=0.3,
                        estOrientQuaternionZ=0.4,
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=9.8,
                    )
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
                        estGravityVectorX=0,
                        estGravityVectorY=0,
                        estGravityVectorZ=-9.8,
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
        d = IMUDataProcessor()
        d.update(data_packets)
        rotations = d._rotated_accelerations
        assert len(rotations) == 3
        # Rotations has 3 arrays in it corresponding to x, y, and z
        # I just could not understand how to get it to work with zip so I did this instead lol
        assert rotations[0][-1] == pytest.approx(expected_value[0])
        assert rotations[1][-1] == pytest.approx(expected_value[1])
        assert rotations[2][-1] == pytest.approx(expected_value[2])

    def test_initial_orientation(self):
        """Tests whether the initial orientation of the rocket is correctly calculated"""
        d = IMUDataProcessor()
        d.update(
            [
                EstimatedDataPacket(
                    1 * 1e9,
                    estLinearAccelX=1,
                    estLinearAccelY=2,
                    estLinearAccelZ=3,
                    estPressureAlt=1,
                    estOrientQuaternionW=0.1,
                    estOrientQuaternionX=0.2,
                    estOrientQuaternionY=0.3,
                    estOrientQuaternionZ=0.4,
                    estGravityVectorX=0.1,
                    estGravityVectorY=-0.6,
                    estGravityVectorZ=9.8,
                ),
            ]
        )

        npt.assert_array_equal(d._current_orientation_quaternions, np.array([0.1, 0.2, 0.3, 0.4]))
        assert d._gravity_upwards_index == 2
        assert d._gravity_direction == -1

        d = IMUDataProcessor()
        d.update(
            [
                EstimatedDataPacket(
                    1 * 1e9,
                    estLinearAccelX=1,
                    estLinearAccelY=2,
                    estLinearAccelZ=3,
                    estPressureAlt=1,
                    estOrientQuaternionW=0.1,
                    estOrientQuaternionX=0.2,
                    estOrientQuaternionY=0.3,
                    estOrientQuaternionZ=0.4,
                    estGravityVectorX=-9.6,
                    estGravityVectorY=-0.6,
                    estGravityVectorZ=0.5,
                ),
            ]
        )

        assert d._gravity_upwards_index == 0
        assert d._gravity_direction == 1


"""
This is unit tests for apogee prediction. Does not work currently, will most likely be moved to
it's own file, because it is not in data_processor.

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
        d = IMUDataProcessor()
        d.update_data([data_packets[0], data_packets[1]])
        ap_pred = ApogeePredictor(set_state, d, [])
        ap_pred.update([data_packets[0], data_packets[1]])
        d.update_data([data_packets[2]])
        ap_pred.update([data_packets[2]])

        velocity = ap_pred._velocity
        assert velocity == pytest.approx(expected_values[0])

        params = ap_pred._params
        assert params == pytest.approx(expected_values[1])

        apogee_pred = ap_pred._apogee_prediction
        assert apogee_pred == pytest.approx(expected_values[2])
"""
