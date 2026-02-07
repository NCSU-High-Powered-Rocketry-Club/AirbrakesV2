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
    """
    Tests for the updated argument parsing function (arg_parser()).
    """

    def test_default_invocation(self, monkeypatch):
        """Tests that running without arguments results in an error."""
        monkeypatch.setattr(sys, "argv", ["main.py"])
        with pytest.raises(SystemExit):
            arg_parser()

    def test_real_mode(self, monkeypatch):
        """Tests the 'real' mode arguments and defaults."""
        monkeypatch.setattr(sys, "argv", ["main.py", "real", "-v", "-s"])

        args = arg_parser()
        assert args.mode == "real"
        assert args.verbose is True
        assert args.debug is False
        assert args.mock_servo is True

    def test_mock_mode_with_mock_firm(self, monkeypatch):
        """Tests 'mock' mode using the new --mock-firm (-m) flag."""
        path_str = "mock/data/log.csv"
        monkeypatch.setattr(sys, "argv", ["main.py", "mock", "-s", "-l", "-f", "-m", path_str])

        args = arg_parser()
        assert args.mode == "mock"
        assert args.real_servo is True
        assert args.keep_log_file is True
        assert args.fast_replay is True
        assert args.mock_firm == Path(path_str)
        assert args.pretend_firm is None  # Should be None when -m is used

    def test_mock_mode_with_pretend_firm(self, monkeypatch):
        """Tests 'mock' mode using the new --pretend-firm (-p) flag."""
        path_str = "mock/data/firm.log"
        monkeypatch.setattr(sys, "argv", ["main.py", "mock", "-p", path_str])

        args = arg_parser()
        assert args.mode == "mock"
        assert args.pretend_firm == Path(path_str)
        assert args.mock_firm is None

    def test_firm_source_exclusivity(self, monkeypatch, capsys):
        """Tests that -m and -p are mutually exclusive in mock mode."""
        monkeypatch.setattr(sys, "argv", ["main.py", "mock", "-m", "path1", "-p", "path2"])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "not allowed with argument" in captured.err

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
            ("real", ["-l"]),
            ("real", ["-f"]),
            ("real", ["-m", "path/to/log"]),
            ("real", ["-p", "path/to/log"]),
        ],
        ids=["real_keep_log", "real_fast_replay", "real_mock_firm", "real_pretend_firm"],
    )
    def test_invalid_args_in_real_mode(self, monkeypatch, mode, args, capsys):
        """Tests that 'real' mode does not accept arguments meant for 'mock'."""
        monkeypatch.setattr(sys, "argv", ["main.py", mode, *args])

        with pytest.raises(SystemExit):
            arg_parser()

        captured = capsys.readouterr()
        assert "unrecognized arguments" in captured.err

    def test_help_output(self, monkeypatch, capsys):
        """Tests that help output reflects current argument naming."""
        # Check Real Help
        monkeypatch.setattr(sys, "argv", ["main.py", "real", "-h"])
        with pytest.raises(SystemExit):
            arg_parser()
        out_real = capsys.readouterr().out
        assert "--mock-servo" in out_real
        assert "--mock-firm" not in out_real

        # Check Mock Help
        monkeypatch.setattr(sys, "argv", ["main.py", "mock", "-h"])
        with pytest.raises(SystemExit):
            arg_parser()
        out_mock = capsys.readouterr().out

        # Checking flags and metavariables individually is more reliable
        # than checking the exact spacing of the combined string.
        assert "--real-servo" in out_mock
        assert "--mock-firm" in out_mock
        assert "--pretend-firm" in out_mock
        assert "LOG_FILE" in out_mock
