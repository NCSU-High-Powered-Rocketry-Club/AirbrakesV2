"""
Textual snapshot tests for the LauncherScreen, i.e. uv run mock.
"""

from typing import cast

from textual.widgets import Input, Switch

from airbrakes.graphics.application import AirbrakesApplication
from airbrakes.graphics.screens.launcher import LauncherScreen, SelectedLaunchConfiguration


class TestLauncherScreen:
    """
    Tests the launcher screen related functions and aesthetics.
    """

    def test_launcher_screen_snap(self, snap_compare, mock_flight_app, terminal_size):
        assert snap_compare(mock_flight_app, terminal_size=terminal_size)

    async def test_keyboard_shortcuts(self, mock_flight_app: AirbrakesApplication):
        """
        Tests the keyboard shortcuts to toggle the switches work correctly.
        """
        async with mock_flight_app.run_test() as pilot:
            await pilot.press("s")
            assert mock_flight_app.screen.query_one("#real-servo-switch", Switch).value

            await pilot.press("c")
            assert mock_flight_app.screen.query_one("#real-camera-switch", Switch).value

            await pilot.press("l")
            assert mock_flight_app.screen.query_one("#keep-log-file-switch", Switch).value

            await pilot.press("f")
            assert mock_flight_app.screen.query_one("#fast-sim-switch", Switch).value

            await pilot.press("t")
            assert mock_flight_app.screen.query_one("#input-target-apogee", Input).has_focus

    async def test_start_button(self, mock_flight_app: AirbrakesApplication, monkeypatch):
        """
        Tests the start button works correctly.
        """
        # We will test with "real_servo" to True to test if params are passed correctly

        selected_file = None
        asserts_ran = False

        async def _receive_launch_configuration(config: SelectedLaunchConfiguration):
            nonlocal asserts_ran
            assert type(config) is SelectedLaunchConfiguration
            assert config.selected_launch == selected_file
            assert config.replay_launch_options is not None
            assert config.replay_launch_options.real_servo is True
            assert config.replay_launch_options.real_camera is False
            assert config.replay_launch_options.keep_log_file is False
            assert config.replay_launch_options.fast_replay is False
            assert config.replay_launch_options.target_apogee is None
            asserts_ran = True

        monkeypatch.setattr(
            mock_flight_app, "_receive_launch_configuration", _receive_launch_configuration
        )

        async with mock_flight_app.run_test() as pilot:
            selected_file = cast("LauncherScreen", pilot.app.screen).selected_file
            await pilot.press("s")  # Switch on real servo
            await pilot.press("r")  # Run the app

        assert asserts_ran

    async def test_benchmark_button(self, mock_flight_app: AirbrakesApplication, monkeypatch):
        """
        Tests the benchmark button works correctly.
        """
        selected_file = None
        asserts_ran = False

        # monkeypatch the run_application method so we don't actually start the program:
        async def mock_run_app():
            nonlocal asserts_ran
            config = mock_flight_app.launch_config
            assert type(config) is SelectedLaunchConfiguration
            assert config.selected_launch == selected_file
            assert config.benchmark_mode is True
            assert config.replay_launch_options is not None
            assert config.replay_launch_options.real_servo is False
            assert config.replay_launch_options.real_camera is False
            assert config.replay_launch_options.keep_log_file is False
            assert config.replay_launch_options.fast_replay is True
            assert config.replay_launch_options.target_apogee is None
            asserts_ran = True

        monkeypatch.setattr(mock_flight_app, "_run_application", mock_run_app)

        async with mock_flight_app.run_test() as pilot:
            selected_file = cast("LauncherScreen", pilot.app.screen).selected_file
            await pilot.press("b")
        assert asserts_ran
