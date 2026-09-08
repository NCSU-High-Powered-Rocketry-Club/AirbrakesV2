"""Regression tests for IMU-derived flight-state processing."""

import numpy as np
import pytest

from airbrakes.constants import (
    GRAVITY_METERS_PER_SECOND_SQUARED,
    SECONDS_UNTIL_PRESSURE_STABILIZATION,
    TRANSONIC_VELOCITY_METERS_PER_SECOND,
    WINDOW_SIZE_FOR_PRESSURE_ZEROING,
)
from airbrakes.data_handling.data_processor import DataProcessor
from tests.auxil.utils import make_estimated_data_packet


class TestDataProcessor:
    """Verify kinematics, pressure selection, and IMU validation."""

    def test_initial_state_and_empty_update_are_safe(self, data_processor):
        data_processor.update([])

        assert data_processor.current_timestamp_seconds == 0.0
        assert data_processor.current_altitude == 0.0
        assert data_processor.vertical_velocity == 0.0
        assert data_processor.max_altitude == 0.0
        assert data_processor.get_processor_data_packets() == []

    def test_first_batched_update_sets_mean_baseline_and_emits_each_packet(self):
        processor = DataProcessor()
        packets = [
            make_estimated_data_packet(timestamp=0, estPressureAlt=100.0),
            make_estimated_data_packet(timestamp=1_000_000_000, estPressureAlt=104.0),
            make_estimated_data_packet(timestamp=2_000_000_000, estPressureAlt=106.0),
        ]

        processor.update(packets)
        processed = processor.get_processor_data_packets()

        assert processor._initial_altitude == pytest.approx(310 / 3)
        assert [packet.current_altitude for packet in processed] == pytest.approx(
            [-310 / 3 + 100, -310 / 3 + 104, -310 / 3 + 106]
        )
        assert [packet.timestamp_seconds for packet in processed] == pytest.approx([0.0, 1.0, 2.0])
        assert [packet.integrating_for_altitude for packet in processed] == ["F", "F", "F"]
        assert processor.max_altitude == pytest.approx(106 - 310 / 3)

    @pytest.mark.parametrize(
        ("timestamps", "expected_altitudes"),
        [
            ([2_000_000_000, 3_000_000_000], [110.0, 120.0]),
            ([2_000_000_000, 2_500_000_000, 3_500_000_000], [110.0, 115.0, 125.0]),
        ],
    )
    def test_integrates_velocity_for_every_packet_in_a_batch(self, timestamps, expected_altitudes):
        processor = DataProcessor()
        processor.update([make_estimated_data_packet(timestamp=1_000_000_000, estPressureAlt=100)])
        processor._previous_altitude = np.float64(100.0)
        processor._previous_vertical_velocity = np.float64(10.0)
        processor.prepare_for_extending_airbrakes()

        processor.update(
            [
                make_estimated_data_packet(timestamp=timestamp, estPressureAlt=999.0)
                for timestamp in timestamps
            ]
        )

        assert processor._current_altitudes == pytest.approx(expected_altitudes)
        assert processor.vertical_velocity == pytest.approx(10.0)
        assert [
            packet.integrating_for_altitude for packet in processor.get_processor_data_packets()
        ] == ["T"] * len(timestamps)

    def test_velocity_and_max_velocity_continue_across_batches(self):
        processor = DataProcessor()
        processor.update([make_estimated_data_packet(timestamp=0, estPressureAlt=100.0)])
        processor.update(
            [
                make_estimated_data_packet(
                    timestamp=1_000_000_000,
                    estPressureAlt=110.0,
                    estCompensatedAccelZ=-19.81,
                )
            ]
        )
        processor.update(
            [
                make_estimated_data_packet(
                    timestamp=2_000_000_000,
                    estPressureAlt=120.0,
                    estCompensatedAccelZ=-9.81,
                )
            ]
        )

        assert processor.vertical_velocity == pytest.approx(10.0)
        assert processor.max_vertical_velocity == pytest.approx(10.0)
        assert processor.current_altitude == pytest.approx(20.0)
        assert processor.max_altitude == pytest.approx(20.0)

    def test_rolling_pressure_baseline_keeps_latest_window(self):
        processor = DataProcessor()
        processor.update(
            [
                make_estimated_data_packet(timestamp=index, estPressureAlt=float(index))
                for index in range(WINDOW_SIZE_FOR_PRESSURE_ZEROING + 1)
            ]
        )
        processor.zero_out_altitude()

        assert len(processor._pressure_alt_buffer) == WINDOW_SIZE_FOR_PRESSURE_ZEROING
        assert processor._initial_altitude == pytest.approx(
            (1 + WINDOW_SIZE_FOR_PRESSURE_ZEROING) / 2
        )

    def test_pressure_fallback_and_post_retraction_recovery(self):
        processor = DataProcessor()
        processor.update([make_estimated_data_packet(timestamp=0, estPressureAlt=100.0)])
        processor.update(
            [
                make_estimated_data_packet(
                    timestamp=1_000_000_000,
                    estPressureAlt=110.0,
                    estCompensatedAccelZ=-19.81,
                )
            ]
        )
        processor.prepare_for_extending_airbrakes()
        processor.update(
            [
                make_estimated_data_packet(
                    timestamp=2_000_000_000,
                    estPressureAlt=1_000.0,
                    estCompensatedAccelZ=-9.81,
                )
            ]
        )

        assert processor.current_altitude == pytest.approx(20.0)
        assert processor.get_processor_data_packets()[-1].integrating_for_altitude == "T"

        processor.prepare_for_retracting_airbrakes()
        processor.update(
            [
                make_estimated_data_packet(
                    timestamp=int((2 + SECONDS_UNTIL_PRESSURE_STABILIZATION / 2) * 1e9),
                    estPressureAlt=2_000.0,
                )
            ]
        )
        assert processor.get_processor_data_packets()[-1].integrating_for_altitude == "T"

        processor.update(
            [
                make_estimated_data_packet(
                    timestamp=int((2 + SECONDS_UNTIL_PRESSURE_STABILIZATION + 0.1) * 1e9),
                    estPressureAlt=130.0,
                )
            ]
        )
        assert processor.current_altitude == pytest.approx(30.0)
        assert processor.get_processor_data_packets()[-1].integrating_for_altitude == "F"

    def test_transonic_selection_switches_per_packet_and_recovers_pressure(self):
        processor = DataProcessor()
        threshold = TRANSONIC_VELOCITY_METERS_PER_SECOND
        processor.update([make_estimated_data_packet(timestamp=0, estPressureAlt=100.0)])
        processor._previous_vertical_velocity = np.float64(threshold)

        processor.update(
            [
                make_estimated_data_packet(timestamp=1_000_000_000, estPressureAlt=110.0),
                make_estimated_data_packet(
                    timestamp=2_000_000_000,
                    estPressureAlt=1_000.0,
                    estCompensatedAccelZ=-(GRAVITY_METERS_PER_SECOND_SQUARED + 1),
                ),
                make_estimated_data_packet(
                    timestamp=3_000_000_000,
                    estPressureAlt=130.0,
                    estCompensatedAccelZ=-(GRAVITY_METERS_PER_SECOND_SQUARED - 1),
                ),
            ]
        )

        assert [
            packet.integrating_for_altitude for packet in processor.get_processor_data_packets()
        ] == [
            "F",
            "T",
            "F",
        ]
        assert processor._current_altitudes == pytest.approx([10.0, 11.0 + threshold, 30.0])

    @pytest.mark.parametrize(
        "field",
        [
            "estPressureAlt",
            "estOrientQuaternionW",
            "estOrientQuaternionX",
            "estOrientQuaternionY",
            "estOrientQuaternionZ",
            "estGravityVectorX",
            "estGravityVectorY",
            "estGravityVectorZ",
            "estAngularRateX",
            "estAngularRateY",
            "estAngularRateZ",
            "estCompensatedAccelX",
            "estCompensatedAccelY",
            "estCompensatedAccelZ",
        ],
    )
    def test_rejects_missing_required_estimator_fields(self, field):
        processor = DataProcessor()

        with pytest.raises(ValueError, match=field):
            processor.update([make_estimated_data_packet(**{field: None})])

    def test_rejects_out_of_order_estimated_packets(self):
        processor = DataProcessor()
        processor.update([make_estimated_data_packet(timestamp=1_000_000_000)])

        with pytest.raises(ValueError, match="chronological"):
            processor.update([make_estimated_data_packet(timestamp=999_999_999)])
