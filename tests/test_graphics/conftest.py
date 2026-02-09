"""
Common fixtures for testing the graphical interface.
"""

import pytest

from airbrakes.graphics.application import AirbrakesApplication


@pytest.fixture
def mock_flight_app(mocked_args_parser) -> AirbrakesApplication:
    return AirbrakesApplication(cmd_args=mocked_args_parser)


@pytest.fixture(params=[(189, 50)], ids=["desktop_full"])
def terminal_size(request):
    """
    The terminal sizes to test the application for.
    """
    return request.param
