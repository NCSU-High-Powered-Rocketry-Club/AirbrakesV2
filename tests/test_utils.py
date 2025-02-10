import sys
from pathlib import Path

import pytest

from airbrakes.utils import arg_parser, deadband


def test_deadband():
    assert deadband(0.1, 0.5) == 0.0
    assert deadband(0.5, 0.5) == 0.5
    assert deadband(1.0, 0.5) == 1.0
    assert deadband(-0.1, 0.5) == 0.0
    assert deadband(-1.0, 0.5) == -1.0


class TestArgumentParsing:
    """Tests for the argument parsing function (arg_parser())."""

    def test_default_invocation(self, monkeypatch):
        """Tests that running the script without arguments results in an error."""
        monkeypatch.setattr(sys, "argv", ["main.py"])

        with pytest.raises(SystemExit):
            arg_parser()

    def test_real_mode(self, monkeypatch):
        """Tests the 'real' mode arguments."""
        monkeypatch.setattr(sys, "argv", ["main.py", "real", "-v"])

        args = arg_parser()
        # This is to ensure that all the arguments are correctly parsed, and to make sure that
        # if you make a change, you update the test.
        assert len(args.__dict__) == 3
        assert args.__dict__.keys() == {"mode", "verbose", "debug"}
        assert args.mode == "real"
        assert args.verbose is True
        assert args.debug is False

    def test_mock_mode(self, monkeypatch):
        """Tests the 'mock' mode arguments."""
        monkeypatch.setattr(
            sys, "argv", ["main.py", "mock", "-r", "-l", "-f", "-c", "-p", "mock/data/path"]
        )

        args = arg_parser()
        # This is to ensure that all the arguments are correctly parsed, and to make sure that
        # if you make a change, you update the test.
        assert len(args.__dict__) == 8
        assert args.__dict__.keys() == {
            "mode",
            "real_servo",
            "keep_log_file",
            "fast_replay",
            "real_camera",
            "path",
            "verbose",
            "debug",
        }
        assert args.mode == "mock"
        assert args.real_servo is True
        assert args.keep_log_file is True
        assert args.fast_replay is True
        assert args.real_camera is True
        assert args.path == Path("mock/data/path")
        assert args.verbose is False
        assert args.debug is False

    def test_sim_mode(self, monkeypatch):
        """Tests the 'sim' mode arguments."""
        monkeypatch.setattr(sys, "argv", ["main.py", "sim", "sub-scale", "-r", "-l", "-f", "-c"])

        args = arg_parser()
        # This is to ensure that all the arguments are correctly parsed, and to make sure that
        # if you make a change, you update the test.
        assert len(args.__dict__) == 8
        assert args.__dict__.keys() == {
            "mode",
            "preset",
            "real_servo",
            "keep_log_file",
            "fast_replay",
            "real_camera",
            "verbose",
            "debug",
        }

        assert args.mode == "sim"
        assert args.preset == "sub-scale"
        assert args.real_servo is True
        assert args.keep_log_file is True
        assert args.fast_replay is True
        assert args.real_camera is True
        assert not hasattr(args, "path")  # `--path` should not be available in `sim` mode

    def test_verbose_and_debug_exclusivity(self, monkeypatch, capsys):
        """Tests that the `-v` and `-d` flags are mutually exclusive."""
        monkeypatch.setattr(sys, "argv", ["main.py", "real", "-v", "-d"])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "not allowed with argument" in captured.err

    @pytest.mark.parametrize(
        ("mode", "args"),
        [
            ("real", ["-r"]),
            ("real", ["-l"]),
            ("real", ["-f"]),
            ("real", ["-c"]),
            ("real", ["-p", "path/to/log"]),
        ],
        ids=[
            "real_with_real_servo",
            "real_with_keep_log",
            "real_with_fast_replay",
            "real_with_real_camera",
            "real_with_path",
        ],
    )
    def test_invalid_args_in_real_mode(self, monkeypatch, mode, args, capsys):
        """Tests that 'real' mode does not accept arguments meant for 'mock' or 'sim'."""
        monkeypatch.setattr(sys, "argv", ["main.py", mode, *args])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "unrecognized arguments" in captured.err

    @pytest.mark.parametrize(
        "args",
        [
            ["mock", "-p", "mock/data/path"],
            ["sim", "-r", "-l", "-f", "-c"],
            ["sim", "legacy", "-r"],
        ],
        ids=["mock_with_path", "sim_with_common_args", "sim_with_preset_and_common_args"],
    )
    def test_shared_arguments(self, monkeypatch, args):
        """Tests that shared arguments are correctly parsed across 'mock' and 'sim'."""
        monkeypatch.setattr(sys, "argv", ["main.py", *args])

        args = arg_parser()
        if "mock" in args.mode:
            assert args.path == Path("mock/data/path")
        elif "sim" in args.mode:
            assert args.preset
            assert not hasattr(args, "path")
            if args.preset == "legacy":
                assert args.real_servo is True
                assert args.keep_log_file is False
                assert args.fast_replay is False
                assert args.real_camera is False
            else:
                assert args.real_servo is True
                assert args.keep_log_file is True
                assert args.fast_replay is True
                assert args.real_camera is True

    def test_sim_default_preset(self, monkeypatch):
        """Tests that the 'sim' mode defaults to 'full-scale' if no preset is provided."""
        monkeypatch.setattr(sys, "argv", ["main.py", "sim"])

        args = arg_parser()
        assert args.mode == "sim"
        assert args.preset == "full-scale"

    def test_help_output(self, monkeypatch, capsys):
        """Tests that help output includes global and subparser-specific arguments."""
        monkeypatch.setattr(sys, "argv", ["main.py", "mock", "-h"])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "-v, --verbose" in captured.out
        assert "-d, --debug" in captured.out
        assert "--real-servo" in captured.out
        assert "--path" in captured.out

        monkeypatch.setattr(sys, "argv", ["main.py", "sim", "-h"])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "-v, --verbose" in captured.out
        assert "-d, --debug" in captured.out
        assert "--real-servo" in captured.out
        assert "--path" not in captured.out  # `--path` should not be in `sim` help
