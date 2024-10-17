import pytest

from utils import convert_to_float, convert_to_nanoseconds, deadband


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
    assert convert_to_float(1) == 1.0
    assert convert_to_float(0.5) == 0.5
    assert convert_to_float("2.5") == 2.5
    assert convert_to_float("invalid") is None
    assert convert_to_float(None) is None


def test_deadband():
    assert deadband(0.1, 0.5) == 0.0
    assert deadband(0.5, 0.5) == 0.5
    assert deadband(1.0, 0.5) == 1.0
    assert deadband(-0.1, 0.5) == 0.0
    assert deadband(-1.0, 0.5) == -1.0
