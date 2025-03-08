"""Module for the finite state machine that represents which state of flight the rocket is in."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from airbrakes.constants import (
    GROUND_ALTITUDE_METERS,
    LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED,
    MAX_ALTITUDE_THRESHOLD,
    MAX_FREE_FALL_SECONDS,
    MAX_VELOCITY_THRESHOLD,
    TAKEOFF_VELOCITY_METERS_PER_SECOND,
    TARGET_APOGEE_METERS,
)
from airbrakes.utils import convert_ns_to_s

if TYPE_CHECKING:
    from airbrakes.context import AirbrakesContext


class State(ABC):
    """
    Abstract Base class for the states of the air brakes system. Each state will have an update
    method that will be called every loop iteration and a next_state method that will be called
    when the state is over.

    For Airbrakes, we will have 5 states:
    1. Standby - when the rocket is on the rail on the ground
    2. Motor Burn - when the motor is burning and the rocket is accelerating
    3. Coast - after the motor has burned out and the rocket is coasting, this is when air brakes
        deployment will be controlled by the bang-bang controller.
    4. Free Fall - when the rocket is falling back to the ground after apogee, this is when the air
        brakes will be retracted.
    5. Landed - when the rocket lands on the ground. After a few seconds in landed state, the
        Airbrakes program will end.
    """

    __slots__ = ("context", "start_time_ns")

    def __init__(self, context: "AirbrakesContext"):
        """
        :param context: The Airbrakes Context managing the state machine.
        """
        self.context = context
        # At the very beginning of each state, we retract the air brakes
        self.context.retract_airbrakes()
        self.start_time_ns = context.data_processor.current_timestamp

    @property
    def name(self):
        """
        :return: The name of the state
        """
        return self.__class__.__name__

    @abstractmethod
    def update(self):
        """
        Called every loop iteration. Uses the Airbrakes Context to interact with the hardware and
        decides when to move to the next state.
        """

    @abstractmethod
    def next_state(self):
        """
        We never expect/want to go back a state e.g. We're never going to go
        from Flight to Motor Burn, so this method just goes to the next state.
        """


class StandbyState(State):
    """
    When the rocket is on the launch rail on the ground.
    """

    __slots__ = ()

    def update(self):
        """
        Checks if the rocket has launched, based on our velocity.
        """

        data = self.context.data_processor
        # If the velocity of the rocket is above a threshold, the rocket has launched.
        if data.vertical_velocity > TAKEOFF_VELOCITY_METERS_PER_SECOND:
            self.next_state()
            return

    def next_state(self):
        self.context.state = MotorBurnState(self.context)


class MotorBurnState(State):
    """
    When the motor is burning and the rocket is accelerating.
    """

    __slots__ = ()

    def __init__(self, context: "AirbrakesContext"):
        super().__init__(context)
        self.context.camera.start_recording()

    def update(self):
        """Checks to see if the velocity has decreased lower than the maximum velocity, indicating
        the motor has burned out."""

        data = self.context.data_processor

        # If our current velocity is less than our max velocity, that means we have stopped
        # accelerating. This is the same thing as checking if our accel sign has flipped
        # We make sure that it is not just a temporary fluctuation by checking if the velocity is a
        # bit less than the max velocity
        if data.vertical_velocity < data.max_vertical_velocity * MAX_VELOCITY_THRESHOLD:
            self.next_state()
            return

    def next_state(self):
        self.context.state = CoastState(self.context)


class CoastState(State):
    """
    When the motor has burned out and the rocket is coasting to apogee. This is the state
    we actually control the air brakes extension.
    """

    __slots__ = ("airbrakes_extended",)

    def __init__(self, context: "AirbrakesContext"):
        super().__init__(context)
        self.airbrakes_extended = False

    def update(self):
        """Checks to see if the rocket has reached apogee, indicating the start of free fall."""

        # In Coast State we start predicting the apogee
        self.context.predict_apogee()

        data = self.context.data_processor

        # This is our bang-bang controller for the air brakes. If we predict we are going to
        # overshoot our target altitude, we extend the air brakes. If we predict we are going to
        # undershoot our target altitude, we retract the air brakes.

        # Gets the latest apogee prediction
        apogee = self.context.last_apogee_predictor_packet.predicted_apogee

        if apogee > TARGET_APOGEE_METERS and not self.airbrakes_extended:
            self.context.extend_airbrakes()
            self.airbrakes_extended = True
        elif apogee <= TARGET_APOGEE_METERS and self.airbrakes_extended:
            self.context.retract_airbrakes()
            self.airbrakes_extended = False

        # if our velocity is zero or negative, we are in free fall.
        if data.vertical_velocity <= 0:
            self.next_state()
            return

        # As backup in case of error, if our current altitude is less than 90% of max altitude, we
        # are in free fall.
        if data.current_altitude <= data.max_altitude * MAX_ALTITUDE_THRESHOLD:
            self.next_state()
            return

    def next_state(self):
        self.context.state = FreeFallState(self.context)


class FreeFallState(State):
    """
    When the rocket is falling back to the ground after apogee.
    """

    __slots__ = ()

    def update(self):
        """Check if the rocket has landed, based on our altitude and a spike in acceleration."""

        data = self.context.data_processor

        # If our altitude is around 0, and we have an acceleration spike, we have landed
        if (
            data.current_altitude <= GROUND_ALTITUDE_METERS
            and data.average_vertical_acceleration >= LANDED_ACCELERATION_METERS_PER_SECOND_SQUARED
        ):
            self.next_state()

        # Sometimes the rocket can land and the altitude will be above the ground altitude threshold
        # This is a fallback condition so that we won't be stuck in freefall state.
        if convert_ns_to_s(data.current_timestamp - self.start_time_ns) >= MAX_FREE_FALL_SECONDS:
            self.next_state()

    def next_state(self):
        self.context.state = LandedState(self.context)


class LandedState(State):
    """
    When the rocket has landed.
    """

    __slots__ = ()

    def update(self):
        """We use this method to stop the air brakes system after we have hit our log buffer."""

        if self.context.logger.is_log_buffer_full:
            self.context.stop()

    def next_state(self):
        # Explicitly do nothing, there is no next state
        pass
