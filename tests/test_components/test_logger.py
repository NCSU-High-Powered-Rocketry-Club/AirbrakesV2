"""Tests for IMU log row construction."""

import pytest

from airbrakes.data_handling.logger import Logger
from airbrakes.state import StandbyState
from tests.auxil.utils import (
    make_context_data_packet,
    make_estimated_data_packet,
    make_processor_data_packet,
    make_raw_data_packet,
    make_servo_data_packet,
)


def test_logger_preserves_raw_and_estimated_packets_with_processor_alignment():
    raw_packet = make_raw_data_packet(timestamp=1, scaledAccelX=1.0)
    estimated_packet = make_estimated_data_packet(timestamp=2, estPressureAlt=100.0)
    processed_packet = make_processor_data_packet(current_altitude=5.0)

    rows = Logger._prepare_logger_packets(
        make_context_data_packet(state=StandbyState),
        make_servo_data_packet(),
        [raw_packet, estimated_packet],
        [processed_packet],
        None,
    )

    assert [row.timestamp for row in rows] == [1, 2]
    assert rows[0].scaledAccelX == 1.0
    assert rows[0].current_altitude is None
    assert rows[1].estPressureAlt == 100.0
    assert rows[1].current_altitude == 5.0


def test_logger_rejects_unaligned_processor_packets():
    with pytest.raises(ValueError, match="align"):
        Logger._prepare_logger_packets(
            make_context_data_packet(state=StandbyState),
            make_servo_data_packet(),
            [make_estimated_data_packet()],
            [],
            None,
        )
