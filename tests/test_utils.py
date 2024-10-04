from airbrakes.utils import convert_to_float, convert_to_nanoseconds, deadband


def test_convert_to_nanoseconds():
    assert convert_to_nanoseconds(1) == 1_000_000_000
    assert convert_to_nanoseconds(0.5) == 500_000_000
    assert convert_to_nanoseconds("2") == 2_000_000_000
    assert convert_to_nanoseconds("invalid") is None
    assert convert_to_nanoseconds(None) is None


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
