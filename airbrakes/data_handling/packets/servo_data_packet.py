"""Data packet containing telemetry from the servo."""

import msgspec


class ServoDataPacket(msgspec.Struct, tag=True, array_like=True):
    """
    A data packet containing information about the servo's current state.
    """

    current_position: float
    """
    The current position of the servo.
    """
    current_temp: float
    """
    The current temperature of the servo.
    """
    voltage: float
    """
    The voltage of the servo.
    """
    system_current_milliamps: float
    """
    The current system current draw.
    """
    battery_volts: float
    """
    The battery voltage.
    """
