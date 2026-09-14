import math
import random
from pathlib import Path

import numpy as np
import numpy.testing as npt
import polars as pl
import pytest
import quaternion

from airbrakes.constants import (
    ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED,
    GRAVITY_METERS_PER_SECOND_SQUARED,
    SECONDS_UNTIL_PRESSURE_STABILIZATION,
    TRANSONIC_VELOCITY_METERS_PER_SECOND,
    WINDOW_SIZE_FOR_PRESSURE_ZEROING,
)
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.packets.imu_data_packet import EstimatedDataPacket
from tests.auxil.utils import make_est_data_packet


def generate_altitude_sine_wave(
    n_points=1000, frequency=0.01, amplitude=100, noise_level=3, base_altitude=20
):
    """
    Generates a random distribution of altitudes that follow a sine wave pattern, with some noise
    added to mimic variations in the readings.

    :param n_points: The number of altitude points to generate.
    :param frequency: The frequency of the sine wave.
    :param amplitude: The amplitude of the sine wave.
    :param noise_level: The standard deviation of the Gaussian noise to add.
    :param base_altitude: The base altitude, i.e. starting altitude from sea level.
    """
    altitudes = []
    for i in range(n_points):
        sine_value = amplitude * math.sin(math.pi * i / (n_points - 1))
        noise = random.gauss(0, noise_level)
        altitudes.append(base_altitude + sine_value + noise)
    return altitudes


def load_data_packets(csv_path: Path, n_packets: int) -> list[EstimatedDataPacket]:
    """
    Reads csv log files containing data packets to use for testing. Will read the first n_packets
    amount of estimated data packets.

    :param csv_path: The relative path of the csv file to read
    :param n_packets: Amount of estimated data packets to retrieve
    :return: list containing n_packets amount of estimated data packets
    """
    data_packets = []
    needed_columns = list(set(EstimatedDataPacket.__struct_fields__) - {"invalid_fields"})
    df = pl.read_csv(csv_path, columns=needed_columns, n_rows=n_packets * 3)

    for row in df.iter_rows(named=True):
        # Convert the named tuple to a dictionary and remove any NaN values:
        row_dict = {k: v for k, v in row.items() if v is not None}
        # Create an EstimatedDataPacket instance from the dictionary
        if row_dict.get("estPressureAlt"):
            data_packets.append(EstimatedDataPacket(**row_dict))
        if len(data_packets) >= n_packets:
            return data_packets

    raise ValueError(f"Could not read {n_packets} packets from {csv_path}")


def make_vertical_motion_packet(
    timestamp_seconds: float,
    pressure_altitude: float,
    vertical_acceleration: float = 0.0,
    *,
    angular_rate=(0.0, 0.0, 0.0),
):
    """
    Create an identity-oriented IMU packet with a requested vertical acceleration.
    This is helpful for testing stuff related to vertical velocity.
    """
    gyro_x, gyro_y, gyro_z = angular_rate
    return make_est_data_packet(
        timestamp=timestamp_seconds * 1e9,
        estCompensatedAccelX=0.0,
        estCompensatedAccelY=0.0,
        estCompensatedAccelZ=-(GRAVITY_METERS_PER_SECOND_SQUARED + vertical_acceleration),
        estPressureAlt=pressure_altitude,
        estOrientQuaternionW=1.0,
        estOrientQuaternionX=0.0,
        estOrientQuaternionY=0.0,
        estOrientQuaternionZ=0.0,
        estGravityVectorX=0.0,
        estGravityVectorY=0.0,
        estGravityVectorZ=GRAVITY_METERS_PER_SECOND_SQUARED,
        estAngularRateX=gyro_x,
        estAngularRateY=gyro_y,
        estAngularRateZ=gyro_z,
    )


@pytest.fixture
def data_processor():
    return DataProcessor()


class TestDataProcessor:
    """Tests the DataProcessor class."""

    def test_slots(self):
        inst = DataProcessor()
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, (np.ndarray, quaternion.quaternion)):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, data_processor):
        d = data_processor
        assert d._max_altitude == 0.0
        assert list(d._vertical_velocities) == [0.0]
        assert d._max_vertical_velocity == 0.0
        assert d._previous_vertical_velocity == 0.0
        assert d._initial_altitude is None
        assert list(d._current_altitudes) == [0.0]
        assert d._last_data_packet is None
        assert d._current_orientation_quaternion is None
        assert list(d._rotated_accelerations) == [0.0]
        assert list(d._vertical_accelerations) == [0.0]
        assert d._data_packets == []
        assert list(d._time_differences) == [0.0]
        assert d._integrating_for_altitude is False
        assert d._integrating_for_altitudes == ["F"]
        assert d._previous_altitude == 0.0
        assert d._retraction_timestamp_seconds is None

        assert d.max_altitude == 0.0
        assert d.current_altitude == 0.0
        assert d.vertical_velocity == 0.0
        assert d.max_vertical_velocity == 0.0
        assert d.current_timestamp_seconds == 0.0
        assert d.average_vertical_acceleration == 0.0
        assert d.average_pitch == 0.0

    def test_first_update_no_data_packets(self, data_processor):
        """
        Tests whether the update() method works correctly, when no data packets are passed.
        """
        d = data_processor
        d.update([])
        assert d._last_data_packet is None
        assert d._data_packets == []
        assert len(d._current_altitudes) == 1
        assert len(d._vertical_velocities) == 1
        assert d.vertical_velocity == 0.0
        assert d.current_altitude == 0.0
        assert d._initial_altitude is None
        assert d._max_altitude == 0.0
        assert d.current_timestamp_seconds == 0.0

    @pytest.mark.parametrize(
        (
            "data_packets",
            "expected_initial_altitude",
            "expected_max_altitude",
            "expected_rotation_quaternion",
            "expected_longitudinal_axis",
        ),
        [
            (
                [
                    make_est_data_packet(
                        timestamp=0,
                        estPressureAlt=20.0,
                        estCompensatedAccelX=0.1,
                        estCompensatedAccelY=0.2,
                        estCompensatedAccelZ=9.79,
                        estOrientQuaternionW=1.123457,
                        estOrientQuaternionX=1.123457,
                        estOrientQuaternionY=1.123457,
                        estOrientQuaternionZ=1.123457,
                    )
                ],
                20.0,
                0.0,
                [1.123457, 1.123457, 1.123457, 1.123457],
                quaternion.quaternion(0, 0, 0, 1),
            ),
            (
                [
                    make_est_data_packet(
                        timestamp=0,
                        estPressureAlt=20.0,
                        estCompensatedAccelX=9.79,
                        estCompensatedAccelY=0.1,
                        estCompensatedAccelZ=0.2,
                        estOrientQuaternionW=-0.976001,
                        estOrientQuaternionX=1.168481,
                        estOrientQuaternionY=1.168481,
                        estOrientQuaternionZ=1.168481,
                    ),
                    make_est_data_packet(
                        timestamp=1_000_000_000,
                        estPressureAlt=30.0,
                    ),
                ],
                25.0,
                5.0,
                [-0.976001, 1.168481, 1.168481, 1.168481],
                quaternion.quaternion(0, 1, 0, 0),
            ),
            (
                [
                    make_est_data_packet(
                        timestamp=0,
                        estPressureAlt=20.0,
                        estCompensatedAccelX=0.1,
                        estCompensatedAccelY=-9.79,
                        estCompensatedAccelZ=0.2,
                        estOrientQuaternionW=-2.222181,
                        estOrientQuaternionX=0.191949,
                        estOrientQuaternionY=0.191949,
                        estOrientQuaternionZ=0.191949,
                    ),
                    make_est_data_packet(
                        timestamp=1_000_000_000,
                        estPressureAlt=30.0,
                    ),
                    make_est_data_packet(
                        timestamp=2_000_000_000,
                        estPressureAlt=40.0,
                    ),
                ],
                30.0,
                10.0,
                [-2.222181, 0.191949, 0.191949, 0.191949],
                quaternion.quaternion(0, 0, -1, 0),
            ),
        ],
    )
    def test_first_update(
        self,
        data_packets,
        expected_initial_altitude,
        expected_max_altitude,
        expected_rotation_quaternion,
        expected_longitudinal_axis,
    ):
        data_processor = DataProcessor()
        data_processor.update(data_packets)

        # Basic packet state
        assert data_processor._last_data_packet == data_packets[-1]
        assert len(data_processor._data_packets) == len(data_packets)

        # Timestamp is exposed in seconds
        assert data_processor.current_timestamp_seconds == pytest.approx(
            data_packets[-1].timestamp / 1e9
        )

        # Internal arrays should contain one value per packet
        assert len(data_processor._vertical_velocities) == len(data_packets)
        assert len(data_processor._current_altitudes) == len(data_packets)
        assert len(data_processor._time_differences) == len(data_packets)
        assert len(data_processor._vertical_accelerations) == len(data_packets)
        assert len(data_processor._rotated_accelerations) == len(data_packets)

        # First packet always starts with zero vertical velocity
        assert data_processor._vertical_velocities[0] == pytest.approx(0.0)

        # Initial and maximum altitude
        assert data_processor._initial_altitude == pytest.approx(expected_initial_altitude)
        assert data_processor.current_altitude == pytest.approx(
            data_processor._current_altitudes[-1]
        )
        assert data_processor.max_altitude == pytest.approx(expected_max_altitude)

        # The first update should use pressure altitude rather than integration
        assert data_processor._integrating_for_altitudes == ["F"] * len(data_packets)

        # Initial orientation quaternion
        npt.assert_allclose(
            quaternion.as_float_array(data_processor._current_orientation_quaternion),
            expected_rotation_quaternion,
            rtol=1e-5,
        )

        # Longitudinal axis determined from the gravity vector
        assert data_processor._longitudinal_axis == expected_longitudinal_axis

        # Average vertical acceleration is calculated from the rotated accelerations
        assert data_processor.average_vertical_acceleration == pytest.approx(
            np.mean(data_processor._rotated_accelerations)
        )

        # Current IMU processor packet fields
        processor_data_packets = data_processor.get_processor_data_packets()

        assert len(processor_data_packets) == len(data_packets)

        for processor_packet, data_packet, expected_altitude in zip(
            processor_data_packets,
            data_packets,
            data_processor._current_altitudes,
            strict=False,
        ):
            assert processor_packet.current_altitude == pytest.approx(expected_altitude)
            assert processor_packet.integrating_for_altitude is False
            assert processor_packet.vertical_velocity_meters_per_s == pytest.approx(
                data_processor._vertical_velocities[data_packets.index(data_packet)]
            )
            assert processor_packet.horizontal_velocity_meters_per_s == pytest.approx(0.0)
            assert processor_packet.tilt_angle_degrees == pytest.approx(
                data_processor.average_pitch
            )
            assert processor_packet.angular_rate_deg_per_s == pytest.approx(0.0)
            assert processor_packet.timestamp_seconds == pytest.approx(data_packet.timestamp / 1e9)

    def test_properties_values(self, data_processor):
        """
        Manually sets internal state to verify properties return correct
        values and types without relying on the complex update() logic.
        """
        d = data_processor
        d._current_altitudes = np.array([100.0])
        d._vertical_velocities = np.array([50.0])
        d._max_altitude = np.float64(150.0)
        d._max_vertical_velocity = np.float64(60.0)
        assert d.current_altitude == 100.0
        assert d.vertical_velocity == 50.0
        assert d.max_altitude == 150.0
        assert d.max_vertical_velocity == 60.0
        assert isinstance(d.current_altitude, float)
        assert isinstance(d.vertical_velocity, float)
        assert isinstance(d.max_altitude, float)
        assert isinstance(d.max_vertical_velocity, float)

    def test_timestamp_safe_access(self, data_processor):
        """
        Tests that timestamp returns 0 if no packet exists, and correct time
        otherwise.
        """
        assert data_processor.current_timestamp_seconds == 0.0
        data_processor._last_data_packet = make_est_data_packet(timestamp=123e9)
        assert data_processor.current_timestamp_seconds == pytest.approx(123.0)

    @pytest.mark.parametrize(
        ("timestamps", "initial_altitude", "initial_velocity", "expected_altitudes"),
        [
            # Test case 1:
            # Dummy packet at 1e9 ns, then two packets at 2e9 and 3e9.
            # dt1 = 1.0 sec, dt2 = 1.0 sec.
            # With a constant vertical velocity of 10 m/s,
            # altitudes will be: [initial_altitude + 10*1, initial_altitude + 10*2]
            ([2.0, 3.0], 100.0, 10.0, [110.0, 120.0]),
            # Test case 2:
            # Dummy packet at 1e9 ns, then three packets at 2e9, 2.5e9, and 3.5e9.
            # dt1 = 1.0 sec, dt2 = 0.5 sec, dt3 = 1.0 sec.
            # Altitude integration: [100+10*1, 100+10*1+10*0.5, 100+10*1+10*0.5+10*1]
            # Expected altitudes: [110, 115, 125]
            ([2.0, 2.5, 3.5], 100.0, 10.0, [110.0, 115.0, 125.0]),
        ],
        ids=["one_second_steps", "mixed_time_steps"],
    )
    def test_calculate_altitude_integration(
        self, data_processor, timestamps, initial_altitude, initial_velocity, expected_altitudes
    ):
        d = data_processor
        d.update([make_vertical_motion_packet(1.0, 100.0)])
        d._previous_altitude = np.float64(initial_altitude)
        d._previous_vertical_velocity = np.float64(initial_velocity)
        d._integrating_for_altitude = True

        packets = [make_vertical_motion_packet(ts, 105.0) for ts in timestamps]
        d.update(packets)
        npt.assert_allclose(d._current_altitudes, expected_altitudes)

    def test_calculate_vertical_velocity(self, data_processor):
        """
        Tests whether the vertical velocity is correctly calculated.
        """
        d = data_processor
        d.update(
            [
                EstimatedDataPacket(
                    2e9,
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
                    2.1e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=-30,
                    estPressureAlt=110,
                    estAngularRateX=-0.8,
                    estAngularRateY=0.05,
                    estAngularRateZ=3.5,
                ),
                EstimatedDataPacket(
                    2.2e9,
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
        assert d._previous_vertical_velocity == pytest.approx(1.9757983, abs=1e-3)
        assert len(d._vertical_velocities) == 3
        assert d._max_vertical_velocity == d.vertical_velocity

        # This tests that we are now falling (the accel is less than 9.8)
        d.update(
            [
                EstimatedDataPacket(
                    5e9,
                    estCompensatedAccelX=0,
                    estCompensatedAccelY=0,
                    estCompensatedAccelZ=30,
                    estPressureAlt=24,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
                EstimatedDataPacket(
                    6e9,
                    estCompensatedAccelX=6,
                    estCompensatedAccelY=7,
                    estCompensatedAccelZ=8,
                    estPressureAlt=25,
                    estAngularRateX=0.01,
                    estAngularRateY=0.02,
                    estAngularRateZ=0.03,
                ),
                EstimatedDataPacket(
                    7e9,
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
        assert d._previous_vertical_velocity == pytest.approx(-138.151733, abs=1e-3)
        assert d.vertical_velocity == pytest.approx(-138.151733, abs=1e-3)
        assert len(d._vertical_velocities) == 3
        # It's falling now so the max velocity should greater than the current velocity
        assert d._max_vertical_velocity > d.vertical_velocity

    def test_vertical_acceleration_deadband(self, data_processor):
        d = data_processor
        d.update(
            [
                make_vertical_motion_packet(
                    0.0,
                    100.0,
                    vertical_acceleration=ACCEL_DEADBAND_METERS_PER_SECOND_SQUARED / 2,
                ),
                make_vertical_motion_packet(1.0, 100.0),
            ]
        )
        assert d._vertical_accelerations[0] == 0.0
        assert d._vertical_accelerations[1] == 0.0

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
        """
        Tests whether the altitude is correctly zeroed.
        """
        d = data_processor
        d._last_data_packet = make_vertical_motion_packet(0.0, altitude_reading[0])
        d._initial_altitude = 20.0
        d._current_orientation_quaternions = quaternion.from_float_array([0.1, 0.1, 0.1, 0.1])
        d._longitudinal_axis = quaternion.quaternion(0, 0, 0, 1)

        packets = [
            make_vertical_motion_packet(i + 3, altitude) for i, altitude in enumerate(altitude_reading)
        ]
        d.update(packets)
        assert d.current_altitude == current_altitude
        assert d._max_altitude == max_altitude

    def test_max_altitude(self, data_processor):
        """
        Tests whether the max altitude is correctly calculated even when altitude decreases.
        """
        d = data_processor
        altitudes = generate_altitude_sine_wave(n_points=1000)
        # run update_data every 10 packets, to mimmick actual data processing in real time:
        for i in range(0, len(altitudes), 10):
            d.update(
                [
                    make_vertical_motion_packet(i + j, alt)
                    for j, alt in enumerate(altitudes[i : i + 10])
                ]
            )
        assert d.max_altitude + d._initial_altitude == pytest.approx(max(altitudes))

    @pytest.mark.parametrize(
        ("csv_path", "expected_value", "n_packets"),
        [
            (Path("tests/imu_data/xminus.csv"), 9.85116094, 2),
            (Path("tests/imu_data/yminus.csv"), 9.83891064, 2),
            (Path("tests/imu_data/zminus.csv"), 9.82264007, 2),
            (Path("tests/imu_data/xplus.csv"), 9.75015129, 2),
            (Path("tests/imu_data/yplus.csv"), 9.61564675, 2),
            (Path("tests/imu_data/zplus.csv"), 9.81399729, 2),
        ],
    )
    def test_calculate_rotations(self, csv_path: Path, expected_value, n_packets: int):
        data_packets = load_data_packets(csv_path, n_packets)
        d = DataProcessor()
        d.update(data_packets)
        assert len(d._rotated_accelerations) == n_packets
        assert d._rotated_accelerations[-1] == pytest.approx(expected_value)

    @pytest.mark.parametrize(
        "launch_data",
        list(Path("launch_data/").glob("*.csv")),
        ids=[p.name for p in Path("launch_data/").glob("*.csv")],
    )
    def test_pitch_calculation(self, data_processor, launch_data):
        """
        Tests that the pitch calculation is correct, this test is kinda lazy and could be better.
        """
        # Load a single est data packet from the CSV file
        d = data_processor
        est_data_packets = load_data_packets(launch_data, 1)
        # Call first update with the loaded packet
        d.update(est_data_packets)
        assert 0.0 <= d.average_pitch <= 5.0, f"Wrong pitch: {d.average_pitch}"

    def test_average_pitch_without_data(self, data_processor):
        assert data_processor.average_pitch == 0.0

    def test_consecutive_updates(self, data_processor):
        """Tests that state updates correctly across multiple calls."""
        d = data_processor

        # 1. First Update (Init)
        d.update([make_vertical_motion_packet(0.0, 10.0)])
        assert d.current_altitude == 0.0
        assert d.max_altitude == 0.0
        # 2. Second Update (Normal flow)
        # Provide a higher altitude
        d.update([make_vertical_motion_packet(1.0, 50.0)])
        assert d.current_altitude == 40.0
        assert d.max_altitude == 40.0
        # 3. Third Update (Lower altitude)
        # Current should drop, Max should stay high
        d.update([make_vertical_motion_packet(2.0, 20.0)])
        assert d.current_altitude == 10.0
        assert d.max_altitude == 40.0

    def test_time_differences_across_updates(self, data_processor):
        d = data_processor
        d.update([make_vertical_motion_packet(1.0, 100.0)])
        d.update(
            [
                make_vertical_motion_packet(2.0, 100.0),
                make_vertical_motion_packet(2.5, 100.0),
                make_vertical_motion_packet(3.5, 100.0),
            ]
        )
        npt.assert_allclose(d._time_differences, [1.0, 0.5, 1.0])
        assert d.current_timestamp_seconds == pytest.approx(3.5)

    def test_prepare_for_extending_then_retracting(self, data_processor):
        """
        Tests whether prepare_for_extending_airbrakes() and prepare_for_retracting_airbrakes() work
        correctly.
        """
        d = data_processor
        assert d._retraction_timestamp_seconds is None
        assert not d._integrating_for_altitude
        d.prepare_for_extending_airbrakes()
        assert d._retraction_timestamp_seconds is None
        assert d._integrating_for_altitude
        d.update([make_vertical_motion_packet(10.0, 100.0)])
        d.prepare_for_retracting_airbrakes()
        assert d._retraction_timestamp_seconds == pytest.approx(10.0)
        assert not d._integrating_for_altitude

    def test_pressure_switch_delay(self, data_processor):
        """
        Tests that pressure altitude is only used after the stabilization window.
        """
        d = data_processor
        d.update([make_vertical_motion_packet(10.0, 100.0)])
        d.prepare_for_retracting_airbrakes()
        half_window = SECONDS_UNTIL_PRESSURE_STABILIZATION / 2
        d.update([make_vertical_motion_packet(10.0 + half_window, 120.0)])
        assert d.current_altitude == pytest.approx(0.0)
        assert d._integrating_for_altitudes == ["T"]

        d.update(
            [
                make_vertical_motion_packet(
                    10.0 + SECONDS_UNTIL_PRESSURE_STABILIZATION + 0.001, 130.0
                )
            ]
        )
        assert d.current_altitude == pytest.approx(30.0)
        assert d._integrating_for_altitudes == ["F"]

    def test_transonic_velocity_threshold(self, data_processor):
        """Tests that transonic altitude integration triggers on absolute vertical velocity."""
        d = data_processor
        threshold = TRANSONIC_VELOCITY_METERS_PER_SECOND
        d.update([make_vertical_motion_packet(0.0, 100.0)])

        # Exactly at the threshold does not trigger integration.
        d.update([make_vertical_motion_packet(1.0, 120.0, threshold)])
        assert d.vertical_velocity == pytest.approx(threshold)
        assert d.current_altitude == pytest.approx(20.0)
        assert d._integrating_for_altitudes == ["F"]

        # Above the threshold switches to integrated altitude.
        d.update([make_vertical_motion_packet(2.0, 1000.0, 1.0)])
        expected_velocity = threshold + 1.0
        assert d.vertical_velocity == pytest.approx(expected_velocity)
        assert d.current_altitude == pytest.approx(20.0 + expected_velocity)
        assert d._integrating_for_altitudes == ["T"]

        # Negative transonic velocity also triggers integration.
        d.update([make_vertical_motion_packet(3.0, 1000.0, -(2 * threshold + 2.0))])
        assert d.vertical_velocity == pytest.approx(-(threshold + 1.0))
        assert d.current_altitude == pytest.approx(20.0)
        assert d._integrating_for_altitudes == ["T"]

        # Returning below threshold switches back to pressure altitude.
        d.update([make_vertical_motion_packet(3.0, 1234.1, 0.0)])
        assert d.current_altitude == pytest.approx(1134.1)
        assert d._integrating_for_altitudes == ["F"]

    def test_transonic_switching_within_batch(self, data_processor):
        """Tests that altitude source selection handles every packet in a batch."""
        d = data_processor
        threshold_velocity = TRANSONIC_VELOCITY_METERS_PER_SECOND + 1.0
        d.update([make_vertical_motion_packet(0.0, 100.0)])
        d.update(
            [
                make_vertical_motion_packet(1.0, 110.0, 0.0),
                make_vertical_motion_packet(2.0, 1000.0, threshold_velocity),
                make_vertical_motion_packet(3.0, 130.0, -threshold_velocity),
            ]
        )
        assert d._current_altitudes == pytest.approx([10.0, 10.0 + threshold_velocity, 30.0])
        processed = d.get_processor_data_packets()
        assert [p.current_altitude for p in processed] == pytest.approx(
            [10.0, 10.0 + threshold_velocity, 30.0]
        )
        assert [p.integrating_for_altitude for p in processed] == ["F", "T", "F"]
        assert d.current_altitude == pytest.approx(30.0)
        assert d.max_altitude == pytest.approx(10.0 + threshold_velocity)

    def test_transonic_switching_and_retract(self, data_processor):
        """Tests that airbrake integration and pressure recovery take precedence over speed."""
        d = data_processor
        transonic_velocity = TRANSONIC_VELOCITY_METERS_PER_SECOND + 1.0
        d.update([make_vertical_motion_packet(0.0, 100.0)])
        d.prepare_for_extending_airbrakes()

        # Keep velocity below transonic while brakes are extended.
        d.update([make_vertical_motion_packet(1.0, 1000.0, 10.0)])
        assert d.current_altitude == pytest.approx(10.0)
        assert d._integrating_for_altitudes == ["T"]

        d.prepare_for_retracting_airbrakes()
        half_window = SECONDS_UNTIL_PRESSURE_STABILIZATION / 2
        t_recovery = 1.0 + half_window
        d.update([make_vertical_motion_packet(t_recovery, 2000.0, 0.0)])
        assert d.current_altitude == pytest.approx(10.0 + 10.0 * half_window)
        assert d._integrating_for_altitudes == ["T"]

        pressure_time = 1.0 + SECONDS_UNTIL_PRESSURE_STABILIZATION + half_window
        d.update([make_vertical_motion_packet(pressure_time, 150.0, 0.0)])
        assert d.current_altitude == pytest.approx(50.0)
        assert d._integrating_for_altitudes == ["F"]

        # Build velocity to exactly transonic-plus-one at the next timestamp.
        transonic_time = 2.75
        dt = transonic_time - pressure_time
        acceleration = (transonic_velocity - d.vertical_velocity) / dt
        d.update([make_vertical_motion_packet(transonic_time, 1000.0, acceleration)])
        assert d.vertical_velocity == pytest.approx(transonic_velocity)
        assert d.current_altitude == pytest.approx(50.0 + transonic_velocity * dt)
        assert d._integrating_for_altitudes == ["T"]

        # Then slow below the threshold and verify pressure altitude resumes.
        below_time = 3.75
        dt = below_time - transonic_time
        acceleration = (10.0 - transonic_velocity) / dt
        d.update([make_vertical_motion_packet(below_time, 180.0, acceleration)])
        assert d.vertical_velocity == pytest.approx(10.0)
        assert d.current_altitude == pytest.approx(80.0)
        assert d._integrating_for_altitudes == ["F"]

    def test_first_update_uses_pressure(self, data_processor):
        """Tests that transonic integration starts from the initialized pressure altitude."""
        transonic_velocity = TRANSONIC_VELOCITY_METERS_PER_SECOND + 1.0
        data_processor.update([make_vertical_motion_packet(0.0, 100.0, transonic_velocity)])
        assert data_processor.vertical_velocity == 0.0
        assert data_processor.current_altitude == pytest.approx(0.0)
        assert data_processor._integrating_for_altitudes == ["F"]

        data_processor.update([make_vertical_motion_packet(1.0, 1000.0, transonic_velocity)])
        assert data_processor.vertical_velocity == pytest.approx(transonic_velocity)
        assert data_processor.current_altitude == pytest.approx(transonic_velocity)
        assert data_processor._integrating_for_altitudes == ["T"]

    def test_get_processor_data_packets_current_fields(self, data_processor):
        d = data_processor
        d.update(
            [
                make_vertical_motion_packet(0.0, 100.0),
                make_vertical_motion_packet(1.0, 110.0),
            ]
        )
        processed = d.get_processor_data_packets()
        assert len(processed) == 2
        assert processed[0].current_altitude == pytest.approx(0.0)
        assert processed[1].current_altitude == pytest.approx(10.0)
        for i, packet in enumerate(processed):
            assert packet.integrating_for_altitude == "F"
            assert packet.vertical_velocity_meters_per_s == pytest.approx(d._vertical_velocities[i])
            assert packet.horizontal_velocity_meters_per_s == 0.0
            assert packet.tilt_angle_degrees == pytest.approx(d.average_pitch)
            assert packet.angular_rate_deg_per_s == 0.0
            assert packet.timestamp_seconds == pytest.approx(float(i))

    def test_integrating_for_altitude_flags_match_each_packet(self, data_processor):
        d = data_processor
        d.update([make_vertical_motion_packet(0.0, 100.0)])
        d.prepare_for_extending_airbrakes()
        d.update(
            [
                make_vertical_motion_packet(1.0, 110.0),
                make_vertical_motion_packet(2.0, 120.0),
            ]
        )
        processed = d.get_processor_data_packets()
        assert [p.integrating_for_altitude for p in processed] == ["T", "T"]
        assert len(processed) == len(d._integrating_for_altitudes) == len(d._data_packets)

    def test_zero_out_altitude(self, data_processor):
        for i in range(1, 11):
            data_processor._data_packets.append(make_vertical_motion_packet(i, i))
        data_processor.zero_out_altitude()
        assert len(data_processor._pressure_alt_buffer) == 10
        assert data_processor._initial_altitude == pytest.approx(5.5)

        # Tests overflow
        for i in range(WINDOW_SIZE_FOR_PRESSURE_ZEROING):
            data_processor._data_packets.append(make_vertical_motion_packet(i, i))
        data_processor.zero_out_altitude()
        assert len(data_processor._pressure_alt_buffer) == WINDOW_SIZE_FOR_PRESSURE_ZEROING

    def test_benchmark_data_processor_update(self, data_processor, benchmark):
        """
        Tests the performance of the update method.
        """
        data_packets = [make_vertical_motion_packet(idx, idx) for idx in range(10)]
        benchmark(data_processor.update, data_packets)
