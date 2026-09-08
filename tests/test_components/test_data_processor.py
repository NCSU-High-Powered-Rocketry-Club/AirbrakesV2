"""Tests for IMU-derived flight-state processing."""

import pytest

from airbrakes.constants import SECONDS_UNTIL_PRESSURE_STABILIZATION
from airbrakes.data_handling.data_processor import DataProcessor
from tests.auxil.utils import make_estimated_data_packet


class TestDataProcessor:
    """Verify the restored IMU kinematics and pressure-altitude behavior."""

    def test_stationary_packet_initializes_without_velocity(self, data_processor):
        packet = make_estimated_data_packet(timestamp=1_000_000_000, estPressureAlt=100.0)
        data_processor.update([packet])

        assert data_processor.current_timestamp_seconds == pytest.approx(1.0)
        assert data_processor.current_altitude == pytest.approx(0.0)
        assert data_processor.vertical_velocity == pytest.approx(0.0)
        assert data_processor.average_pitch == pytest.approx(180.0)

    def test_integrates_rotated_acceleration_across_batches(self):
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

        assert processor.vertical_velocity == pytest.approx(10.0)
        assert processor.current_altitude == pytest.approx(10.0)
        assert processor.max_vertical_velocity == pytest.approx(10.0)

    def test_rolling_pressure_baseline_updates_in_standby(self):
        processor = DataProcessor()
        processor.update(
            [
                make_estimated_data_packet(timestamp=0, estPressureAlt=100.0),
                make_estimated_data_packet(timestamp=1, estPressureAlt=102.0),
            ]
        )
        processor.zero_out_altitude()

        assert processor._initial_altitude == pytest.approx(101.0)

    def test_airbrake_pressure_fallback_and_recovery(self):
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
                    timestamp=int((2 + SECONDS_UNTIL_PRESSURE_STABILIZATION + 0.1) * 1e9),
                    estPressureAlt=130.0,
                )
            ]
        )
        assert processor.current_altitude == pytest.approx(30.0)
        assert processor.get_processor_data_packets()[-1].integrating_for_altitude == "F"

    def test_requires_complete_estimated_kinematics(self):
        processor = DataProcessor()
        with pytest.raises(ValueError, match="estOrientQuaternionW"):
            processor.update([make_estimated_data_packet(estOrientQuaternionW=None)])
