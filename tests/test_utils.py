import sys
from pathlib import Path

import pytest

from airbrakes.utils import arg_parser, convert_str_to_float, convert_to_nanoseconds, deadband


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ("1", 1),
        ("0.5", 500_000_000),
        ("invalid", None),
    ],
    ids=["string_int_input", "string_float_input", "invalid"],
)
def test_convert_to_nanoseconds_correct_inputs(input_value, expected):
    assert convert_to_nanoseconds(input_value) == expected


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (1, 1),
        (0.5, 0),
    ],
    ids=[
        "int_input",
        "float_input",
    ],
)
def test_convert_to_nanoseconds_wrong_inputs(input_value, expected):
    assert convert_to_nanoseconds(input_value) == expected


def test_convert_to_float():
    assert convert_str_to_float(1) == 1.0
    assert convert_str_to_float(0.5) == 0.5
    assert convert_str_to_float("2.5") == 2.5
    assert convert_str_to_float("invalid") is None
    assert convert_str_to_float(None) is None


def test_deadband():
    assert deadband(0.1, 0.5) == 0.0
    assert deadband(0.5, 0.5) == 0.5
    assert deadband(1.0, 0.5) == 1.0
    assert deadband(-0.1, 0.5) == 0.0
    assert deadband(-1.0, 0.5) == -1.0


class TestArgumentParsing:
    """Tests for the argument parsing function (arg_parser())."""

    def test_init(self, monkeypatch):
        """Tests the default values of the argument parser."""

        # Mock sys.argv to simulate no arguments being passed to the script
        monkeypatch.setattr(sys, "argv", ["main.py"])

        args = arg_parser()
        assert args.__dict__ == {
            "mock": False,
            "real_servo": False,
            "keep_log_file": False,
            "fast_replay": False,
            "debug": False,
            "path": None,
            "verbose": False,
        }

    @pytest.mark.parametrize(
        "mock_invocation",
        [True, False],
        ids=["uv-method", "legacy-method"],
    )
    def test_mock_invocation(self, monkeypatch, mock_invocation):
        """Tests the mock invocation of the script."""

        # Mock sys.argv to simulate the script being run in mock mode
        monkeypatch.setattr(sys, "argv", ["main.py", "-m"])

        args = arg_parser(mock_invocation=mock_invocation)
        assert args.mock is True
        assert args.real_servo is False
        assert args.keep_log_file is False
        assert args.fast_replay is False
        assert args.debug is False
        assert args.path is None
        assert args.verbose is False

    def test_path_argument(self, monkeypatch):
        """Tests the path argument of the script."""

        # Mock sys.argv to simulate the script being run with the path argument
        monkeypatch.setattr(sys, "argv", ["main.py", "-m", "-p", "path/to/log"])

        args = arg_parser()
        assert args.mock is True
        assert args.real_servo is False
        assert args.keep_log_file is False
        assert args.fast_replay is False
        assert args.debug is False
        assert isinstance(args.path, Path)
        assert args.path == Path("path/to/log")
        assert args.verbose is False

    def test_mutually_exclusive_verbose_and_debug(self, monkeypatch, capsys):
        """Tests that the verbose and debug flags are mutually exclusive."""

        # Mock sys.argv to simulate the script being run with both verbose and debug flags
        monkeypatch.setattr(sys, "argv", ["main.py", "-v", "-d"])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "options cannot be used together" in captured.err

    @pytest.mark.parametrize(
        "arg_type",
        [["--real-servo"], ["--keep-log-file"], ["--fast-replay"], ["--path", "a/path"]],
        ids=["real_servo", "keep_log_file", "fast_replay", "path"],
    )
    def test_args_only_available_with_mock_invocation(self, monkeypatch, capsys, arg_type):
        """Tests that the arguments that are only available in mock replay mode are not available
        in real mode."""

        # Mock sys.argv to simulate the script being run with the real servo flag
        monkeypatch.setattr(sys, "argv", ["main.py", *arg_type])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "only available in mock replay mode" in captured.err
