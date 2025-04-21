"""
Tests the camera module.
"""

import pytest


@pytest.fixture
def both_cameras(request):
    """
    Fixture that returns both the Camera and MockCamera classes (if you specify them).
    """
    return request.getfixturevalue(request.param)


class TestCamera:
    """
    Tests the Camera class.

    This tests the base methods, which are common between the Camera and MockCamera classes.
    """

    @pytest.mark.parametrize("both_cameras", ["camera", "mock_camera"], indirect=True)
    def test_slots(self, both_cameras):
        inst = both_cameras
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_start(self, mock_camera):
        mock_camera.start()
        assert mock_camera.camera_control_process.is_alive()
        assert mock_camera.is_running
        assert not mock_camera.stop_context_event.is_set()
        assert not mock_camera.motor_burn_started.is_set()
        mock_camera.stop()

    def test_stop(self, mock_camera):
        mock_camera.start()
        mock_camera.stop()
        assert not mock_camera.is_running
        assert mock_camera.stop_context_event.is_set()
        assert mock_camera.motor_burn_started.is_set()

    def test_start_recording(self, mock_camera):
        mock_camera.start_recording()
        assert not mock_camera.is_running
        assert mock_camera.motor_burn_started.is_set()
