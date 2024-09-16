import pytest

from airbrakes.airbrakes import AirbrakesContext


@pytest.fixture
def airbrakes_context(imu, logger, servo):
    return AirbrakesContext(logger, servo, imu)


class TestAirbrakesContext:
    """Tests the AirbrakesContext class"""

    def test_slots(self, airbrakes_context):
        inst = airbrakes_context
        for attr in inst.__slots__:
            assert getattr(inst, attr, "err") != "err", f"got extra slot '{attr}'"

    def test_init(self, airbrakes_context, logger, imu, servo):
        assert airbrakes_context.logger == logger
        assert airbrakes_context.servo == servo
        assert airbrakes_context.imu == imu
