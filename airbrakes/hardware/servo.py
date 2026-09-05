"""
Module which contains the Servo class, representing a servo motor that
controls the extension of the airbrakes.
"""

import contextlib
import threading

#from turtle import speed
import numpy as np

# Can only be imported on Linux:
with contextlib.suppress(ImportError):
    import gpiod

from rpi_hardware_pwm import HardwarePWM

from airbrakes.base_classes.base_servo import BaseServo
from airbrakes.constants import (
    AIR_DENSITY_KG_PER_M3,
    AIRBRAKE_DRAG_COEFFICIENT,
    AIRBRAKE_EXTENSIONS,
    AIRBRAKE_SURFACE_AREAS_IN2,
    CHIP_PATH,
    I2C_ADDRESS,
    I2C_BUS,
    MAX_AIRBRAKE_FORCE_LBS,
    MAX_EXPECTED_AMPS,
    SERVO_DELAY_SECONDS,
    SERVO_MAX_ANGLE_DEGREES,
    SERVO_MAX_PULSE_WIDTH_US,
    SERVO_MIN_ANGLE_DEGREES,
    SERVO_MIN_PULSE_WIDTH_US,
    SERVO_OPERATING_FREQUENCY_HZ,
    SERVO_SWITCH_PIN,
    SHUNT_OHMS,
    ServoExtension,
)


class Servo(BaseServo):
    """
    A custom class that represents a servo motor.
    The servo controls the extension of airbrakes.

    The servo we use is the DS3235, which is a coreless digital servo.
    We only use one servo to control the airbrakes, using hardware PWM
    on the Pi 5.
    """

    __slots__ = (
        "_current_angle",
        "_go_to_max_no_buzz",
        "_go_to_min_no_buzz",
        "current_extension",
        "ina",
        "servo",
        "servo_line",
    )

    def __init__(self, servo_channel: int) -> None:
        """
        Initializes the Servo class.

        :param servo_channel: The PWM channel that the servo is
            connected to.
        """
        self.current_extension: ServoExtension = ServoExtension.MIN_NO_BUZZ
        self._go_to_max_no_buzz: threading.Timer | None = None
        self._go_to_min_no_buzz: threading.Timer | None = None

        # Request control of a GPIO pin from the kernel
        self.servo_line = gpiod.request_lines(
            path=CHIP_PATH,
            consumer="airbrakes-servo",
            config={SERVO_SWITCH_PIN: gpiod.LineSettings(direction=gpiod.line.Direction.OUTPUT)},
        )

        self.servo = HardwarePWM(pwm_channel=servo_channel, hz=SERVO_OPERATING_FREQUENCY_HZ, chip=0)

        # This library fails to import on Windows due to smbus2:
        from ina219 import INA219  # noqa: PLC0415

        self.ina = INA219(
            shunt_ohms=SHUNT_OHMS,
            address=I2C_ADDRESS,
            max_expected_amps=MAX_EXPECTED_AMPS,
            busnum=I2C_BUS,
        )
        self.ina.configure(
            # sample the current faster (84us per sample instead of 532us per sample with ADC_12BIT,
            # which is the default setting). We lose about ~8mA of resolution.
            shunt_adc=INA219.ADC_9BIT
        )
        self._current_angle = float(ServoExtension.MIN_NO_BUZZ.value)

    def start(self) -> None:
        """
        Starts the servo by starting the PWM signal with the initial duty cycle
        corresponding to the minimum extension without buzzing.
        """
        # Switch on the servo switch
        self.servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.ACTIVE)

        self.servo.start(self._angle_to_duty_cycle(ServoExtension.MIN_NO_BUZZ.value))

    def stop(self) -> None:
        """
        Stops the servo by stopping the PWM signal.
        """
        self._cancel_timer("_go_to_max_no_buzz")
        self._cancel_timer("_go_to_min_no_buzz")

        # Switch off the servo switch
        self.servo_line.set_value(SERVO_SWITCH_PIN, gpiod.line.Value.INACTIVE)

        self.servo.stop()

        # Release the gpio pin back to the kernel
        self.servo_line.release()

    def extend_airbrakes(self, velocity: float) -> None:
        """Extends the airbrakes to the maximum safe extension for the rocket's current velocity."""
        self._cancel_timer("_go_to_min_no_buzz")

        extension = self._calculate_deployment_extension(velocity)
        angle = self._extension_to_angle(extension)

        self._set_angle(angle)

    def _calculate_deployment_extension(self, velocity: float) -> float:
        speed = abs(velocity)

        if speed == 0:
            return 1.0

        max_force_newtons = MAX_AIRBRAKE_FORCE_LBS * 4.44822

        max_area_m2 = (
            2 * max_force_newtons
            / (
                AIR_DENSITY_KG_PER_M3
                * speed**2
                * AIRBRAKE_DRAG_COEFFICIENT
            )
        )

        max_area_in2 = max_area_m2 / 0.00064516

        max_area_in2 = np.clip(
            max_area_in2,
            AIRBRAKE_SURFACE_AREAS_IN2[0],
            AIRBRAKE_SURFACE_AREAS_IN2[-1],
        )

        extension = np.interp(
            max_area_in2,
            AIRBRAKE_SURFACE_AREAS_IN2,
            AIRBRAKE_EXTENSIONS,
        )

        return float(extension)

    def _extension_to_angle(self, extension: float) -> float:
        extension = max(0.0, min(1.0, extension))

        min_angle = ServoExtension.MIN_NO_BUZZ.value
        max_angle = ServoExtension.MAX_NO_BUZZ.value

        return min_angle + extension * (max_angle - min_angle)

    def retract_airbrakes(self) -> None:
        """
        Retracts the servo to the minimum extension.
        """
        self._cancel_timer("_go_to_max_no_buzz")
        self._set_extension(ServoExtension.MIN_EXTENSION)
        self._go_to_min_no_buzz = threading.Timer(
            SERVO_DELAY_SECONDS, self._set_extension, args=(ServoExtension.MIN_NO_BUZZ,)
        )
        self._go_to_min_no_buzz.start()

    def _set_angle(self, angle: float) -> None:
        """Sets the servo to a specific angle in degrees."""
        self._current_angle = angle
        duty_cycle = self._angle_to_duty_cycle(angle)
        self.servo.change_duty_cycle(duty_cycle)

    def _set_extension(self, extension: ServoExtension) -> None:
        """Sets the servo extension and corresponding PWM duty cycle."""
        self.current_extension = extension
        self._current_angle = float(extension.value)

        duty_cycle: float = self._angle_to_duty_cycle(extension.value)
        self.servo.change_duty_cycle(duty_cycle)

    def _cancel_timer(self, timer_name: str) -> None:
        """Cancels the pending transition stored in the named timer slot."""
        timer = getattr(self, timer_name)
        if timer is not None:
            timer.cancel()

    @property
    def servo_extension(self) -> ServoExtension:
        """
        Gets the extension most recently commanded to the servo.

        :return: The commanded servo extension.
        """
        return self.current_extension

    @property
    def servo_angle(self) -> float:
        """Gets the most recently commanded servo angle."""
        return self._current_angle

    @property
    def battery_volts(self) -> float:
        """
        Gets the battery voltage from the INA219 sensor.

        :return: The battery voltage in volts.
        """
        return self.ina.supply_voltage()

    @property
    def system_current_milliamps(self) -> float:
        """
        Gets the current system current draw from the INA219 sensor.

        :return: The current system current draw in milliamps.
        """
        return self.ina.current()

    @staticmethod
    def _angle_to_pulse_width(angle: float) -> float:
        """
        Converts an angle in degrees to a pulse width in microseconds for a
        servo motor.

        :param angle: The angle in degrees (0 to 180).
        :return: The corresponding pulse width in microseconds.
        """
        # Clamp the angle to the valid range:
        angle = max(SERVO_MIN_ANGLE_DEGREES, min(SERVO_MAX_ANGLE_DEGREES, angle))

        return SERVO_MIN_PULSE_WIDTH_US + (
            (SERVO_MAX_PULSE_WIDTH_US - SERVO_MIN_PULSE_WIDTH_US)
            * (angle - SERVO_MIN_ANGLE_DEGREES)
            / (SERVO_MAX_ANGLE_DEGREES - SERVO_MIN_ANGLE_DEGREES)
        )

    @staticmethod
    def _angle_to_duty_cycle(angle: float) -> float:
        """
        Converts an angle in degrees to a duty cycle percentage for a servo
        motor.

        :param angle: The angle in degrees.
        :return: The corresponding duty cycle percentage.
        """
        pulse_us = Servo._angle_to_pulse_width(angle)

        duty_cycle: float = (pulse_us / (1_000_000 / SERVO_OPERATING_FREQUENCY_HZ)) * 100
        return duty_cycle
