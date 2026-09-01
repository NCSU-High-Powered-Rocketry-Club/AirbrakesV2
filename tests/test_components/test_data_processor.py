import math
import random
from typing import TYPE_CHECKING

import numpy as np
import polars as pl
import pytest
import quaternion

from airbrakes.constants import (
    SECONDS_UNTIL_PRESSURE_STABILIZATION,
    TRANSONIC_VELOCITY_METERS_PER_SECOND,
)
from airbrakes.data_handling.data_processor import DataProcessor
from airbrakes.data_handling.packets.processor_data_packet import ProcessorDataPacket
from tests.auxil.utils import make_firm_data_packet, make_processor_data_packet_zeroed

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


def load_data_packets(csv_path: Path, n_packets: int) -> list[ProcessorDataPacket]:
    """
    Reads csv log files containing data packets to use for testing. Will
    read the first n_packets amount of estimated data packets.

    :param csv_path: The relative path of the csv file to read
    :param n_packets: Amount of estimated data packets to retrieve
    :return: list containing n_packets amount of estimated data packets
    """
    data_packets = []
    needed_columns = list(
        set(ProcessorDataPacket.__struct_fields__) - {"invalid_fields", "integrating_for_altitude"}
    )
    df = pl.read_csv(
        csv_path,
        columns=needed_columns,
        n_rows=n_packets * 3,
    )

    for row in df.iter_rows(named=True):
        # Convert the named tuple to a dictionary and remove any NaN values:
        row_dict = {k: v for k, v in row.items() if v is not None}
        row_dict["integrating_for_altitude"] = "F"
        # Create an ProcessorDataPacket instance from the dictionary
        if row_dict.get("current_altitude"):
            packet = ProcessorDataPacket(**row_dict)
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
        make_processor_data_packet_zeroed(
            current_altitude=1,
            vertical_velocity_meters_per_s=1,
            horizontal_velocity_meters_per_s=1,
            tilt_angle_degrees=1,
            angular_rate_deg_per_s=1,
        ),
        make_processor_data_packet_zeroed(
            current_altitude=2,
            vertical_velocity_meters_per_s=2,
            horizontal_velocity_meters_per_s=2,
            tilt_angle_degrees=2,
            angular_rate_deg_per_s=2,
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
        assert d._integrating_for_altitudes == ["F"]
        assert d._last_data_packet is None
        assert d._data_packets == []

        # Test properties on init
        assert d.max_altitude == 0.0
        assert d.current_altitude == 0.0
        assert d.vertical_velocity == 0.0
        assert d.max_vertical_velocity == 0.0
        assert d.current_timestamp_seconds == 0

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
                        est_position_z_meters=0,
                        est_velocity_z_meters_per_s=20,
                    )
                ],
                0.0,
            ),
            (
                [
                    make_firm_data_packet(
                        est_position_z_meters=1,
                        est_velocity_z_meters_per_s=20,
                    ),
                    make_firm_data_packet(
                        est_position_z_meters=2,
                        est_velocity_z_meters_per_s=30,
                    ),
                ],
                0.5,
            ),
            (
                [
                    make_firm_data_packet(
                        est_position_z_meters=1,
                        est_velocity_z_meters_per_s=20,
                    ),
                    make_firm_data_packet(
                        est_position_z_meters=2,
                        est_velocity_z_meters_per_s=30,
                    ),
                    make_firm_data_packet(
                        est_position_z_meters=3,
                        est_velocity_z_meters_per_s=40,
                    ),
                ],
                1.0,
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

        # On first update, arrays are initialized from the full batch.
        assert len(d._current_altitudes) == len(data_packets)
        assert len(d._vertical_velocities) == len(data_packets)
        assert d._integrating_for_altitudes == ["F"] * len(data_packets)

        assert d._vertical_velocities[0] == data_packets[0].est_velocity_z_meters_per_s

        initial_altitude = np.mean([packet.est_position_z_meters for packet in data_packets])
        expected_current_altitude = data_packets[-1].est_position_z_meters - initial_altitude
        assert d.current_altitude == pytest.approx(expected_current_altitude)
        assert d._max_altitude == pytest.approx(max_alt)
        assert d.max_altitude == pytest.approx(max_alt)

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
        initial_altitude = np.mean(altitudes[:10])
        assert d.max_altitude == pytest.approx(max(altitudes) - initial_altitude)

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
        assert d.current_altitude == 0.0
        assert d.max_altitude == 0.0

        # 2. Second Update (Normal flow)
        # Provide a higher altitude
        d.update([make_firm_data_packet(est_position_z_meters=50)])
        assert d.current_altitude == 40.0
        assert d.max_altitude == 40.0

        # 3. Third Update (Lower altitude)
        # Current should drop, Max should stay high
        d.update([make_firm_data_packet(est_position_z_meters=20)])
        assert d.current_altitude == 10.0
        assert d.max_altitude == 40.0

    def test_pressure_switch_delay(self, data_processor) -> None:
        """
        Tests that pressure altitude is only used after the stabilization window.
        """
        d = data_processor

        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=10.0,
                    est_position_z_meters=0.0,
                    est_velocity_z_meters_per_s=5.0,
                )
            ]
        )
        d.prepare_for_retracting_airbrakes()
        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=10.5,
                    est_position_z_meters=20.0,
                    est_velocity_z_meters_per_s=5.0,
                )
            ]
        )
        assert d.current_altitude == pytest.approx(2.5)
        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=11.0,
                    est_position_z_meters=30.0,
                    est_velocity_z_meters_per_s=5.0,
                )
            ]
        )
        assert d.current_altitude == pytest.approx(30.0)

    def test_transonic_velocity_threshold(self, data_processor) -> None:
        """Tests that transonic altitude integration uses the velocity magnitude."""
        d = data_processor
        threshold = TRANSONIC_VELOCITY_METERS_PER_SECOND

        initial_altitude = 100.0

        d.update(
            [make_firm_data_packet(timestamp_seconds=0.0, est_position_z_meters=initial_altitude)]
        )
        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=1.0,
                    est_position_z_meters=120.0,
                    est_velocity_z_meters_per_s=threshold,
                )
            ]
        )
        # First we test that the altitude is still using pressure altitude, since the velocity is
        # not above the threshold.
        assert d.current_altitude == pytest.approx(20.0)

        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=2.0,
                    est_position_z_meters=1_000.0,
                    est_velocity_z_meters_per_s=threshold + 1.0,
                )
            ]
        )
        # Then we test that the altitude is now integrating the velocity, since it is above the
        # threshold.
        assert d.current_altitude == pytest.approx(20.0 + threshold + 1.0)

        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=3.0,
                    est_position_z_meters=1_000.0,
                    est_velocity_z_meters_per_s=-(threshold + 1.0),
                )
            ]
        )
        # Also lets test it with negative just in case we are some how falling at transonic speeds
        assert d.current_altitude == pytest.approx(20.0)

        new_altitude = 1234.1
        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=3.0,
                    est_position_z_meters=new_altitude,
                    est_velocity_z_meters_per_s=1.0,
                )
            ]
        )
        # Finally lets test that we can switch back to pressure altitude
        assert d.current_altitude == pytest.approx(new_altitude - initial_altitude)

    def test_transonic_switching_within_batch(self, data_processor) -> None:
        """Tests that altitude source selection handles every packet in a batch."""
        d = data_processor
        transonic_velocity = TRANSONIC_VELOCITY_METERS_PER_SECOND + 1.0

        d.update([make_firm_data_packet(timestamp_seconds=0.0, est_position_z_meters=100.0)])
        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=1.0,
                    est_position_z_meters=110.0,
                    est_velocity_z_meters_per_s=0.0,
                ),
                make_firm_data_packet(
                    timestamp_seconds=2.0,
                    est_position_z_meters=1_000.0,
                    est_velocity_z_meters_per_s=transonic_velocity,
                ),
                make_firm_data_packet(
                    timestamp_seconds=3.0,
                    est_position_z_meters=130.0,
                    est_velocity_z_meters_per_s=0.0,
                ),
            ]
        )

        # This just tests that it does the switching on a per-packet basis, and that the altitude
        assert d._current_altitudes == pytest.approx([10.0, 10.0 + transonic_velocity, 30.0])
        assert [
            packet.current_altitude for packet in d.get_processor_data_packets()
        ] == pytest.approx([10.0, 10.0 + transonic_velocity, 30.0])
        assert [packet.integrating_for_altitude for packet in d.get_processor_data_packets()] == [
            "F",
            "T",
            "F",
        ]
        assert d.current_altitude == pytest.approx(30.0)
        assert d.max_altitude == pytest.approx(10.0 + transonic_velocity)

    def test_transonic_switching_and_retract(self, data_processor) -> None:
        """Tests that airbrake integration and pressure recovery take precedence over speed."""
        d = data_processor
        transonic_velocity = TRANSONIC_VELOCITY_METERS_PER_SECOND + 1.0

        initial_timestamp = 1.0
        current_velocity = 10.0

        d.update([make_firm_data_packet(timestamp_seconds=0.0, est_position_z_meters=100.0)])
        d.prepare_for_extending_airbrakes()
        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=initial_timestamp,
                    est_position_z_meters=1_000.0,
                    est_velocity_z_meters_per_s=current_velocity,
                )
            ]
        )
        # We check that even though the velocity is below the transonic threshold, the altitude is
        # still integrated because we're about to extend the airbrakes
        assert d.current_altitude == pytest.approx(current_velocity * initial_timestamp)
        assert d.get_processor_data_packets()[-1].integrating_for_altitude == "T"

        dt = SECONDS_UNTIL_PRESSURE_STABILIZATION / 2.0

        d.prepare_for_retracting_airbrakes()
        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=initial_timestamp + dt,
                    est_position_z_meters=2_000.0,
                    est_velocity_z_meters_per_s=current_velocity,
                )
            ]
        )
        # We're still integrating because the airbrakes are still in the process of
        # retracting
        assert d.current_altitude == pytest.approx(
            current_velocity * initial_timestamp + current_velocity * dt
        )
        assert d.get_processor_data_packets()[-1].integrating_for_altitude == "T"

        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=initial_timestamp + dt + SECONDS_UNTIL_PRESSURE_STABILIZATION,
                    est_position_z_meters=150.0,
                    est_velocity_z_meters_per_s=10.0,
                )
            ]
        )
        # Now that the airbrakes have fully retracted, we should be back to using pressure altitude
        assert d.current_altitude == pytest.approx(50.0)
        assert d.get_processor_data_packets()[-1].integrating_for_altitude == "F"

        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=2.75,
                    est_position_z_meters=1_000.0,
                    est_velocity_z_meters_per_s=transonic_velocity,
                )
            ]
        )
        # Now that the velocity is above the transonic threshold, we should be integrating again
        assert d.current_altitude == pytest.approx(50.0 + transonic_velocity)
        assert d.get_processor_data_packets()[-1].integrating_for_altitude == "T"

        d.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=3.75,
                    est_position_z_meters=180.0,
                    est_velocity_z_meters_per_s=10.0,
                )
            ]
        )
        # Finally, we should be back to using pressure altitude, since the airbrakes have fully
        # retracted and the velocity is below the transonic threshold
        assert d.current_altitude == pytest.approx(80.0)
        assert d.get_processor_data_packets()[-1].integrating_for_altitude == "F"

    def test_first_update_uses_pressure(self, data_processor) -> None:
        """Tests that transonic integration starts from the initialized pressure altitude."""
        transonic_velocity = TRANSONIC_VELOCITY_METERS_PER_SECOND + 1.0

        data_processor.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=0.0,
                    est_position_z_meters=100.0,
                    est_velocity_z_meters_per_s=transonic_velocity,
                )
            ]
        )
        assert data_processor.current_altitude == pytest.approx(0.0)
        assert data_processor.get_processor_data_packets()[-1].integrating_for_altitude == "F"

        data_processor.update(
            [
                make_firm_data_packet(
                    timestamp_seconds=1.0,
                    est_position_z_meters=1_000.0,
                    est_velocity_z_meters_per_s=transonic_velocity,
                )
            ]
        )
        assert data_processor.current_altitude == pytest.approx(transonic_velocity)
