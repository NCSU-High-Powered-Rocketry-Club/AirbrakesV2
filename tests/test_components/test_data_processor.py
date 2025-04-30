import math
import random
from pathlib import Path

import numpy as np
import numpy.testing as npt
import pandas as pd
import pytest
import scipy.spatial

from airbrakes.mock.mock_imu import MockIMU
from airbrakes.telemetry.data_processor import DataProcessor
from airbrakes.telemetry.packets.imu_data_packet import EstimatedDataPacket
from tests.auxil.utils import make_est_data_packet


def generate_altitude_sine_wave(
    n_points=1000, frequency=0.01, amplitude=100, noise_level=3, base_altitude=20
):
    """Generates a random distribution of altitudes that follow a sine wave pattern, with some
    noise added to mimic variations in the readings.

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


def load_data_packets(csv_path: Path, n_packets: int) -> list[EstimatedDataPacket]:
    """Reads csv log files containing data packets to use for testing. Will read the first
    n_packets amount of estimated data packets.

    :param csv_path: The relative path of the csv file to read
    :param n_packets: Amount of estimated data packets to retrieve
    :return: list containing n_packets amount of estimated data packets
    """
    data_packets = []
    needed_columns = list(set(EstimatedDataPacket.__struct_fields__) - {"invalid_fields"})
    df = pd.read_csv(
        csv_path,
        usecols=needed_columns,
        converters={"invalid_fields": MockIMU._convert_invalid_fields},
        chunksize=n_packets * 3,
    )

    with df:
        for chunk in df:
            for row in chunk.itertuples(index=False):
                # Convert the named tuple to a dictionary and remove any NaN values:
                row_dict = {k: v for k, v in row._asdict().items() if pd.notna(v)}
                # Create an EstimatedDataPacket instance from the dictionary
                if row_dict.get("estPressureAlt"):
                    packet = EstimatedDataPacket(**row_dict)
                else:
                    continue
                data_packets.append(packet)

                if len(data_packets) >= n_packets:
                    return data_packets

    raise ValueError(f"Could not read {n_packets} packets from {csv_path}")


@pytest.fixture
def data_processor():
    return DataProcessor()


class TestDataProcessor:
    """Tests the DataProcessor class"""

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
        inst = DataProcessor()
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, np.ndarray):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, data_processor):
        """Tests whether the DataProcessor is correctly initialized"""
        d = data_processor
        # Test attributes on init
        assert d._max_altitude == 0.0
        assert isinstance(d._vertical_velocities, np.ndarray)
        assert list(d._vertical_velocities) == [0.0]
        assert d._max_vertical_velocity == 0.0
        assert d._previous_vertical_velocity == 0.0
        assert d._initial_altitude is None
        assert isinstance(d._current_altitudes, np.ndarray)
        assert list(d._current_altitudes) == [0.0]
        assert d._last_data_packet is None
        assert d._current_orientation_quaternions is None
        assert isinstance(d._rotated_accelerations, np.ndarray)
        assert d._rotated_accelerations == np.array([0.0])
        assert d._data_packets == []
        assert isinstance(d._time_differences, np.ndarray)
        assert list(d._time_differences) == [0.0]

        assert d._integrating_for_altitude is False
        assert d._previous_altitude == 0.0
        assert d._retraction_timestamp is None

        # Test properties on init
        assert d.max_altitude == 0.0
        assert d.current_altitude == 0.0
        assert d.vertical_velocity == 0.0
        assert d.max_vertical_velocity == 0.0
        assert d.current_timestamp == 0
        assert d.average_vertical_acceleration == 0.0

    @pytest.mark.parametrize(
        ("packets", "initial_altitude", "initial_velocity", "expected_altitudes"),
        [
            # Test case 1:
            # Dummy packet at 1e9 ns, then two packets at 2e9 and 3e9.
            # dt1 = 1.0 sec, dt2 = 1.0 sec.
            # With a constant vertical velocity of 10 m/s,
            # altitudes will be: [initial_altitude + 10*1, initial_altitude + 10*2]
            (
                [(2e9, -9.8, 105), (3e9, -9.8, 105)],
                100.0,
                10.0,
                [110.0, 120.0],
            ),
            # Test case 2:
            # Dummy packet at 1e9 ns, then three packets at 2e9, 2.5e9, and 3.5e9.
            # dt1 = 1.0 sec, dt2 = 0.5 sec, dt3 = 1.0 sec.
            # Altitude integration: [100+10*1, 100+10*1+10*0.5, 100+10*1+10*0.5+10*1]
            # Expected altitudes: [110, 115, 125]
            (
                [(2e9, -9.8, 105), (2.5e9, -9.8, 105), (3.5e9, -9.8, 105)],
                100.0,
                10.0,
                [110.0, 115.0, 125.0],
            ),
        ],
    )
    def test_calculate_altitude_integration(
        self, data_processor, packets, initial_altitude, initial_velocity, expected_altitudes
    ):
        """
        Tests whether altitude integration (using a simple Riemann sum of vertical velocity * dt)
        is computed correctly when integrating for altitude is enabled.
        """
        d = data_processor

        # Perform a dummy update to establish initial conditions.
        # This avoids calling _first_update() during our test.
        dummy_packet = make_est_data_packet(
            timestamp=1e9,  # 1 second in ns
            estCompensatedAccelX=0,
            estCompensatedAccelY=0,
            estCompensatedAccelZ=-9.8,  # so that rotated acceleration becomes 9.8 m/s²
            estPressureAlt=100.0,
            estOrientQuaternionW=1,
            estOrientQuaternionX=0,
            estOrientQuaternionY=0,
            estOrientQuaternionZ=0,
            estAngularRateX=0,
            estAngularRateY=0,
            estAngularRateZ=0,
        )
        d.update([dummy_packet])

        # Set our known initial conditions.
        d._previous_altitude = initial_altitude
        d._previous_vertical_velocity = initial_velocity

        # Force the altitude integration branch to run.
        d._integrating_for_altitude = True

        # Build new data packets based on the parameterized input.
        # Each tuple is (timestamp, estCompensatedAccelZ, estPressureAlt).
        # We use zero angular rates and identity orientation (quaternion = [1,0,0,0])
        new_packets = []
        for ts, accel_z, pressure_alt in packets:
            new_packets.append(
                make_est_data_packet(
                    timestamp=ts,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=accel_z,
                    estPressureAlt=pressure_alt,
                    estOrientQuaternionW=1,
                    estOrientQuaternionX=0,
                    estOrientQuaternionY=0,
                    estOrientQuaternionZ=0,
                    estAngularRateX=0,
                    estAngularRateY=0,
                    estAngularRateZ=0,
                )
            )

        # Update with the new packets.
        d.update(new_packets)

        # When integrating, the altitude is computed as:
        #     altitude = previous_altitude + cumsum(vertical_velocity * dt)
        # In our test, because the rotated acceleration comes out as 9.8 m/s²,
        # deadband(9.8 - 9.8, ...) returns 0, so the vertical velocity remains constant.
        # Thus, with a constant vertical velocity, altitude should increase linearly.
        computed_altitudes = d._current_altitudes

        # Compare each computed altitude with the expected value.
        for computed, expected in zip(computed_altitudes, expected_altitudes, strict=False):
            assert computed == pytest.approx(expected)

    def test_calculate_vertical_velocity(self, data_processor):
        """Tests whether the vertical velocity is correctly calculated"""
        d = data_processor
        assert d.vertical_velocity == 0.0
        assert d._max_vertical_velocity == d.vertical_velocity
        assert d._previous_vertical_velocity == 0

        d.update(
            [
                # reference data is interest launch (very rounded data)
                EstimatedDataPacket(
                    2 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=70,
                    estPressureAlt=106,
                    estOrientQuaternionW=0.35,
                    estOrientQuaternionX=-0.036,
                    estOrientQuaternionY=-0.039,
                    estOrientQuaternionZ=0.936,
                    estGravityVectorX=0,
                    estGravityVectorY=0,
                    estGravityVectorZ=9.8,
                    estAngularRateX=-0.17,
                    estAngularRateY=0.18,
                    estAngularRateZ=3.7,
                ),
                EstimatedDataPacket(
                    2.1 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=-30,
                    estPressureAlt=110,
                    estAngularRateX=-0.8,
                    estAngularRateY=0.05,
                    estAngularRateZ=3.5,
                ),
                EstimatedDataPacket(
                    2.2 * 1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=-10,
                    estPressureAlt=123,
                    estAngularRateX=-0.08,
                    estAngularRateY=-0.075,
                    estAngularRateZ=3.4,
                ),
            ]
        )
        # we use pytest.approx() because of floating point errors
        assert d._previous_vertical_velocity == pytest.approx(1.971628)
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
        assert d._previous_vertical_velocity == pytest.approx(-138.0245)
        assert d.vertical_velocity == pytest.approx(-138.0245)
        assert len(d._vertical_velocities) == 3
        # It's falling now so the max velocity should greater than the current velocity
        assert d._max_vertical_velocity > d.vertical_velocity

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
        assert d.current_timestamp == 0

    @pytest.mark.parametrize(
        ("data_packets", "init_alt", "max_alt", "rotation_quat", "expected_longitudinal_axis"),
        [
            (
                [
                    make_est_data_packet(
                        timestamp=0 * 1e9,
                        estPressureAlt=20,
                        estGravityVectorX=0.1,
                        estGravityVectorY=0.2,
                        estGravityVectorZ=9.79,
                    )
                ],
                20.0,
                0.0,
                np.array([0.5, 0.5, 0.5, 0.5]),
                np.array([0, 0, 1]),
            ),
            (
                [
                    make_est_data_packet(
                        timestamp=1 * 1e9,
                        estPressureAlt=20,
                        estGravityVectorX=9.79,
                        estGravityVectorY=0.1,
                        estGravityVectorZ=0.2,
                    ),
                    make_est_data_packet(
                        timestamp=2 * 1e9,
                        estPressureAlt=30,
                    ),
                ],
                25.0,
                5.0,
                np.array([-0.434374, 0.520038, 0.520038, 0.520038]),
                np.array([1, 0, 0]),
            ),
            (
                [
                    make_est_data_packet(
                        timestamp=1 * 1e9,
                        estPressureAlt=20,
                        estGravityVectorX=0.1,
                        estGravityVectorY=-9.79,
                        estGravityVectorZ=0.2,
                    ),
                    make_est_data_packet(
                        timestamp=2 * 1e9,
                        estPressureAlt=30,
                    ),
                    make_est_data_packet(
                        timestamp=3 * 1e9,
                        estPressureAlt=40,
                    ),
                ],
                30.0,
                10.0,
                np.array([-0.988993, 0.085428, 0.085428, 0.085428]),
                np.array([0, -1, 0]),
            ),
        ],
        ids=["one_data_packet", "two_data_packets", "three_data_packets"],
    )
    def test_first_update(
        self,
        data_processor,
        data_packets,
        init_alt,
        max_alt,
        rotation_quat,
        expected_longitudinal_axis,
    ):
        """
        Tests whether the update() method works correctly, for the first update() call,
        along with get_processor_data_packets()
        """
        d = data_processor
        d.update(data_packets.copy())
        # We should always have a last data point
        assert d._last_data_packet
        assert d._last_data_packet == data_packets[-1]
        assert len(d._data_packets) == len(data_packets)
        assert d.current_timestamp == data_packets[-1].timestamp

        # the max() is there because if we only process one data packet, we just return early
        # and the variables set at __init__ are used:
        assert len(d._current_altitudes) == max(len(data_packets), 1)
        assert len(d._vertical_velocities) == max(len(data_packets), 1)
        assert len(d._vertical_velocities) == len(d._current_altitudes)
        # Our initial velocity should always be zero, since we set the previous data point to the
        # first data point, giving a time difference of zero, and hence a velocity of zero, and thus
        # implicitly testing it.
        assert d._vertical_velocities[0] == 0.0

        assert d._initial_altitude == init_alt
        assert isinstance(d._current_orientation_quaternions, scipy.spatial.transform.Rotation)
        npt.assert_allclose(
            d._current_orientation_quaternions.as_quat(scalar_first=True),
            rotation_quat,
            rtol=1e-5,
        )
        assert d.current_altitude == (
            0.0 if init_alt is None else data_packets[-1].estPressureAlt - init_alt
        )
        assert d._max_altitude == d.max_altitude == max_alt

        processed_data = d.get_processor_data_packets()
        assert len(processed_data) == len(data_packets)
        for idx, data in enumerate(processed_data):
            assert data.current_altitude == d._current_altitudes[idx]
            assert data.vertical_velocity == d._vertical_velocities[idx]
            assert data.vertical_acceleration == d._rotated_accelerations[idx]
            assert data.time_since_last_data_packet == d._time_differences[idx]

        assert d.average_vertical_acceleration == np.mean(d._rotated_accelerations)
        assert d._longitudinal_axis.all() == expected_longitudinal_axis.all()

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
    def test_altitude_zeroing(
        self, data_processor, altitude_reading, current_altitude, max_altitude
    ):
        """Tests whether the altitude is correctly zeroed"""
        d = data_processor
        # test_first_update tests the initial alt update, so we can skip that here:
        d._last_data_packet = make_est_data_packet(
            timestamp=0,
            estPressureAlt=altitude_reading[0],
        )
        d._initial_altitude = 20.0
        d._current_orientation_quaternions = scipy.spatial.transform.Rotation.from_quat(
            [0.1, 0.1, 0.1, 0.1]
        )

        new_packets = [
            make_est_data_packet(
                timestamp=idx + 3,
                estPressureAlt=alt,
                estOrientQuaternionW=0.1,
                estOrientQuaternionX=0.2,
                estOrientQuaternionY=0.3,
                estOrientQuaternionZ=0.4,
            )
            for idx, alt in enumerate(altitude_reading)
        ]
        d.update(new_packets)
        assert d.current_altitude == current_altitude
        assert d._max_altitude == max_altitude

    def test_max_altitude(self, data_processor):
        """Tests whether the max altitude is correctly calculated even when altitude decreases"""
        d = data_processor
        altitudes = generate_altitude_sine_wave(n_points=1000)
        # run update_data every 10 packets, to mimmick actual data processing in real time:
        for i in range(0, len(altitudes), 10):
            d.update(
                [
                    make_est_data_packet(
                        timestamp=i,
                        estPressureAlt=alt,
                    )
                    for alt in altitudes[i : i + 10]
                ]
            )
        assert d.max_altitude + d._initial_altitude == pytest.approx(max(altitudes))

    @pytest.mark.parametrize(
        ("csv_path", "expected_value", "n_packets"),
        [
            (
                Path("tests/imu_data/xminus.csv"),
                9.85116094,
                2,
            ),
            (
                Path("tests/imu_data/yminus.csv"),
                9.83891064,
                2,
            ),
            (
                Path("tests/imu_data/zminus.csv"),
                9.82264007,
                2,
            ),
            (
                Path("tests/imu_data/xplus.csv"),
                9.75015129,
                2,
            ),
            (
                Path("tests/imu_data/yplus.csv"),
                9.61564675,
                2,
            ),
            (
                Path("tests/imu_data/zplus.csv"),
                9.81399729,
                2,
            ),
        ],
    )
    def test_calculate_rotations(self, csv_path: Path, expected_value, n_packets: int):
        data_packets = load_data_packets(csv_path, n_packets)
        d = DataProcessor()
        d.update(data_packets)
        rotations = d._rotated_accelerations
        assert len(rotations) == n_packets

        assert rotations[-1] == pytest.approx(expected_value)

    def test_benchmark_data_processor_update(self, data_processor, benchmark):
        """Tests the performance of the update method"""
        data_packets = [
            make_est_data_packet(
                timestamp=idx,
                estPressureAlt=idx,
            )
            for idx in range(10)
        ]
        benchmark(data_processor.update, data_packets)

    def test_prepare_for_extending_then_retracting(self, data_processor):
        """
        Tests whether prepare_for_extending_airbrakes() and prepare_for_retracting_airbrakes() work
        correctly
        """
        d = data_processor
        assert d._retraction_timestamp is None
        assert not d._integrating_for_altitude
        d.prepare_for_extending_airbrakes()
        assert d._retraction_timestamp is None
        assert d._integrating_for_altitude
        d.prepare_for_retracting_airbrakes()
        assert d._retraction_timestamp is not None
        assert not d._integrating_for_altitude

    @pytest.mark.parametrize(
        "launch_data",
        [
            *list(Path("launch_data/").glob("*.csv")),
        ],
        ids=[
            *[p.name for p in Path("launch_data/").glob("*.csv")],
        ],
    )
    def test_pitch_calculation(self, data_processor, launch_data):
        """Tests that the pitch calculation is correct"""
        # Load a single est data packet from the CSV file
        d = data_processor
        est_data_packets = load_data_packets(launch_data, 1)
        # Call first update with the loaded packet
        d.update(est_data_packets)
        assert 0.0 <= d.average_pitch <= 5.0, f"Wrong pitch: {d.average_pitch}"
