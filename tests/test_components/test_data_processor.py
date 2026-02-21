import math
import random
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
import pytest
import quaternion
from firm_client import FIRMDataPacket

from airbrakes.data_handling.data_processor import DataProcessor
from tests.auxil.utils import make_firm_data_packet, make_firm_data_packet_zeroed

if TYPE_CHECKING:
    from pathlib import Path


def generate_altitude_sine_wave(
    n_points=1000, frequency=0.01, amplitude=100, noise_level=3, base_altitude=20
):
    """
    Generates a random distribution of altitudes that follow a sine wave
    pattern, with some noise added to mimic variations in the readings.

    :param n_points: The number of altitude points to generate.
    :param frequency: The frequency of the sine wave.
    :param amplitude: The amplitude of the sine wave.
    :param noise_level: The standard deviation of the Gaussian noise to
        add.
    :param base_altitude: The base altitude, i.e. starting altitude from
        sea level.
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


def load_data_packets(csv_path: Path, n_packets: int) -> list[FIRMDataPacket]:
    """
    Reads csv log files containing data packets to use for testing. Will
    read the first n_packets amount of estimated data packets.

    :param csv_path: The relative path of the csv file to read
    :param n_packets: Amount of estimated data packets to retrieve
    :return: list containing n_packets amount of estimated data packets
    """
    data_packets = []
    needed_columns = list(set(FIRMDataPacket.__struct_fields__) - {"invalid_fields"})
    df = pl.read_csv(
        csv_path,
        columns=needed_columns,
        n_rows=n_packets * 3,
    )

    for row in df.iter_rows(named=True):
        # Convert the named tuple to a dictionary and remove any NaN values:
        row_dict = {k: v for k, v in row.items() if v is not None}
        # Create an FIRMDataPacket instance from the dictionary
        if row_dict.get("est_position_z_meters"):
            packet = FIRMDataPacket(**row_dict)
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
    """Tests the DataProcessor class."""

    packets = [
        make_firm_data_packet_zeroed(
            timestamp_seconds=1,
            est_acceleration_x_gs=1,
            est_acceleration_y_gs=2,
            est_acceleration_z_gs=3,
            est_position_z_meters=20,
            est_quaternion_w=0.1,
            est_quaternion_x=0.2,
            est_quaternion_y=0.3,
            est_quaternion_z=0.4,
        ),
        make_firm_data_packet_zeroed(
            timestamp_seconds=2,
            est_acceleration_x_gs=2,
            est_acceleration_y_gs=3,
            est_acceleration_z_gs=4,
            est_position_z_meters=21,
            est_quaternion_w=0.1,
            est_quaternion_x=0.2,
            est_quaternion_y=0.3,
            est_quaternion_z=0.4,
        ),
    ]

    def test_slots(self):
        inst = DataProcessor()
        for attr in inst.__slots__:
            val = getattr(inst, attr, "err")
            if isinstance(val, np.ndarray | quaternion.quaternion):
                continue
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, data_processor):
        """Tests whether the DataProcessor is correctly initialized."""
        d = data_processor
        # Test attributes on init
        assert d._max_altitude == 0.0
        assert isinstance(d._vertical_velocities, np.ndarray)
        assert list(d._vertical_velocities) == [0.0]
        assert d._max_vertical_velocity == 0.0
        assert isinstance(d._current_altitudes, np.ndarray)
        assert list(d._current_altitudes) == [0.0]
        assert d._last_data_packet is None
        assert isinstance(d._vertical_accelerations, np.ndarray)
        assert d._vertical_accelerations == np.array([0.0])
        assert d._data_packets == []

        # Test properties on init
        assert d.max_altitude == 0.0
        assert d.current_altitude == 0.0
        assert d.vertical_velocity == 0.0
        assert d.max_vertical_velocity == 0.0
        assert d.current_timestamp_seconds == 0
        assert d.average_vertical_acceleration == 0.0

    def test_first_update_no_data_packets(self, data_processor):
        """
        Tests whether the update() method works correctly, when no data
        packets are passed.
        """
        d = data_processor
        d.update([])
        assert d._last_data_packet is None
        assert len(d._data_packets) == 0
        assert len(d._current_altitudes) == 1
        assert len(d._vertical_velocities) == 1
        assert d.vertical_velocity == 0.0, "velocity should be the same as set in __init__"
        assert d.current_altitude == 0.0, "Current altitude should be the same as set in __init__"
        assert d._max_altitude == 0.0
        assert d._last_data_packet is None
        assert d.current_timestamp_seconds == 0

    @pytest.mark.parametrize(
        ("data_packets", "max_alt"),
        [
            (
                [
                    make_firm_data_packet(
                        timestamp_seconds=0,
                        est_position_z_meters=20,
                    )
                ],
                20.0,
            ),
            (
                [
                    make_firm_data_packet(
                        timestamp_seconds=1,
                        est_position_z_meters=20,
                    ),
                    make_firm_data_packet(
                        timestamp_seconds=2,
                        est_position_z_meters=30,
                    ),
                ],
                30.0,
            ),
            (
                [
                    make_firm_data_packet(
                        timestamp_seconds=1,
                        est_position_z_meters=20,
                    ),
                    make_firm_data_packet(
                        timestamp_seconds=2,
                        est_position_z_meters=30,
                    ),
                    make_firm_data_packet(
                        timestamp_seconds=3,
                        est_position_z_meters=40,
                    ),
                ],
                40.0,
            ),
        ],
        ids=["one_data_packet", "two_data_packets", "three_data_packets"],
    )
    def test_first_update(
        self,
        data_processor,
        data_packets,
        max_alt,
    ):
        """
        Tests whether the update() method works correctly, for the first
        update() call, along with get_processor_data_packets().
        """
        d = data_processor
        d.update(data_packets.copy())
        # We should always have a last data point
        assert d._last_data_packet
        assert d._last_data_packet == data_packets[-1]
        assert len(d._data_packets) == len(data_packets)
        assert d.current_timestamp_seconds == data_packets[-1].timestamp_seconds

        # On the first update we set the first values directly from the last data packet and return
        assert len(d._current_altitudes) == 1
        assert len(d._vertical_velocities) == 1

        assert d._vertical_velocities[0] == data_packets[0].est_velocity_z_meters_per_s
        assert d.current_altitude == data_packets[-1].est_position_z_meters
        assert d._max_altitude == d.max_altitude == max_alt

    def test_max_altitude(self, data_processor):
        """
        Tests whether the max altitude is correctly calculated even when
        altitude decreases.
        """
        d = data_processor
        altitudes = generate_altitude_sine_wave(n_points=1000)
        for i in range(0, len(altitudes), 10):
            d.update(
                [
                    make_firm_data_packet(
                        timestamp_seconds=i,
                        est_position_z_meters=alt,
                    )
                    for alt in altitudes[i : i + 10]
                ]
            )
        assert d.max_altitude == pytest.approx(max(altitudes))

    def test_properties_values(self, data_processor):
        """
        Manually sets internal state to verify properties return correct
        values and types without relying on the complex update() logic.
        """
        d = data_processor
        d._current_altitudes = np.array([100.0])
        d._vertical_velocities = np.array([50.0])
        d._vertical_accelerations = np.array([10.0, 20.0])
        d._max_altitude = np.float64(150.0)
        d._max_vertical_velocity = np.float64(60.0)

        assert d.current_altitude == 100.0
        assert d.vertical_velocity == 50.0
        assert d.average_vertical_acceleration == 15.0  # Mean of 10 and 20
        assert d.max_altitude == 150.0
        assert d.max_vertical_velocity == 60.0
        assert isinstance(d.current_altitude, float)

    def test_timestamp_safe_access(self, data_processor):
        """
        Tests that timestamp returns 0 if no packet exists, and correct time
        otherwise.
        """
        assert data_processor.current_timestamp_seconds == 0

        data_processor._last_data_packet = make_firm_data_packet(timestamp_seconds=123)
        assert data_processor.current_timestamp_seconds == 123

    def test_consecutive_updates(self, data_processor):
        """Tests that state updates correctly across multiple calls."""
        d = data_processor

        # 1. First Update (Init)
        d.update([make_firm_data_packet(est_position_z_meters=10)])
        assert d.max_altitude == 10.0

        # 2. Second Update (Normal flow)
        # Provide a higher altitude
        d.update([make_firm_data_packet(est_position_z_meters=50)])
        assert d.current_altitude == 50.0
        assert d.max_altitude == 50.0

        # 3. Third Update (Lower altitude)
        # Current should drop, Max should stay high
        d.update([make_firm_data_packet(est_position_z_meters=20)])
        assert d.current_altitude == 20.0
        assert d.max_altitude == 50.0
