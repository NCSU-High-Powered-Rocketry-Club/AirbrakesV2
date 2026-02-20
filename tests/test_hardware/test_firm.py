import pytest

from tests.conftest import IdleFIRM


class TestFIRM:
    """
    Really all the FIRM class is, is a wrapper for firm-client, which has extensive unit tests.
    TODO: could probably write unit tests using firm-client's mock port.
    """

    def test_slots(self):
        """Ensure we strictly define slots to prevent memory bloat."""
        firm = IdleFIRM()
        for attr in firm.__slots__:
            hasattr(firm, attr)

        # Verify we can't add random attributes
        with pytest.raises(AttributeError):
            firm.random_new_attr = 5
