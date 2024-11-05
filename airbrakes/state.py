"""Module for the finite state machine that represents which state of flight we are in."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from constants import (
    GROUND_ALTITUDE,
    MAX_VELOCITY_THRESHOLD,
    MOTOR_BURN_TIME,
    TAKEOFF_HEIGHT,
    TAKEOFF_VELOCITY,
    TARGET_ALTITUDE,
)

if TYPE_CHECKING:
    from airbrakes.airbrakes import AirbrakesContext


class State(ABC):
    """
    Abstract Base class for the states of the airbrakes system. Each state will have an update
    method that will be called every loop iteration and a next_state method that will be called
    when the state is over.

    For Airbrakes, we will have 4 states:
    1. Stand By - when the rocket is on the rail on the ground
    2. Motor Burn - when the motor is burning and the rocket is accelerating
    3. Flight - when the motor has burned out and the rocket is coasting, this is when air brakes
        will be deployed.
    4. Free Fall - when the rocket is falling back to the ground after apogee, this is when the air
        brakes will be retracted.
    """

    __slots__ = ("context", "start_time_ns")

    def __init__(self, context: "AirbrakesContext"):
        """
        :param context: The state context object that will be used to interact with the electronics
        """
        self.context = context
        # At the very beginning of each state, we retract the airbrakes
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
        Called every loop iteration. Uses the context to interact with the hardware and decides
        when to move to the next state.
        """

    @abstractmethod
    def next_state(self):
        """
        We never expect/want to go back a state e.g. We're never going to go
        from Flight to Motor Burn, so this method just goes to the next state.
        """


class StandbyState(State):
    """
    When the rocket is on the rail on the ground.
    """

    __slots__ = ()

    def update(self):
        """
        Checks if the rocket has launched, based on our velocity and altitude.
        """
        # We need to check if the rocket has launched, if it has, we move to the next state.
        # For that we can check:
        # 1) Velocity - If the velocity of the rocket is above a threshold, the rocket has
        # launched.
        # 2) Altitude - If the altitude is above a threshold, the rocket has launched.
        # Ideally we would directly communicate with the motor, but we don't have that capability.

        data = self.context.data_processor

        if data.vertical_velocity > TAKEOFF_VELOCITY:
            self.next_state()
            return

        if data.current_altitude > TAKEOFF_HEIGHT:
            self.next_state()
            return

    def next_state(self):
        self.context.state = MotorBurnState(self.context)


class MotorBurnState(State):
    """
    When the motor is burning and the rocket is accelerating.
    """

    def update(self):
        """Checks to see if the acceleration has dropped to zero, indicating the motor has
        burned out."""

        data = self.context.data_processor

        # If our current velocity is less than our max velocity, that means we have stopped
        # accelerating. This is the same thing as checking if our accel sign has flipped
        # We make sure that it is not just a temporary fluctuation by checking if the velocity is a
        # bit less than the max velocity
        if (
            data.vertical_velocity
            < data.max_vertical_velocity - data.max_vertical_velocity * MAX_VELOCITY_THRESHOLD
        ):
            self.next_state()
            return

        # Fallback: if our motor has burned for longer than its burn time, go to the next state
        if data.current_timestamp - self.start_time_ns > MOTOR_BURN_TIME * 1e9:
            self.next_state()

    def next_state(self):
        self.context.state = CoastState(self.context)


class CoastState(State):
    """
    When the motor has burned out and the rocket is coasting to apogee. This is the state
    we actually extend the airbrakes.
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

        # if our prediction is overshooting our target altitude, extend the airbrakes
        if self.context.apogee_predictor.apogee > TARGET_ALTITUDE:
            self.context.extend_airbrakes()

        # if our velocity is close to zero or negative, we are in free fall.
        if data.vertical_velocity <= 0:
            self.next_state()
            return

        # As backup in case of error, if our current altitude is less than 90% of max altitude, we
        # are in free fall.
        if data.current_altitude <= data.max_altitude * 0.9:
            self.next_state()
            return

    def next_state(self):
        # This also retracts the airbrakes:
        self.context.state = FreeFallState(self.context)


class FreeFallState(State):
    """
    When the rocket is falling back to the ground after apogee.
    """

    __slots__ = ()

    def update(self):
        """Check if the rocket has landed, based on our altitude."""

        data = self.context.data_processor

        # If our altitude is 0, we have landed:
        if data.current_altitude <= GROUND_ALTITUDE:
            self.next_state()

    def next_state(self):
        self.context.state = LandedState(self.context)


class LandedState(State):
    """
    When the rocket has landed.
    """

    __slots__ = ()

    def update(self):
        """We use this method to stop the airbrakes system after we have hit our log buffer."""

        if self.context.logger.is_log_buffer_full:
            self.context.stop()

    def next_state(self):
        # Explicitly do nothing, there is no next state
        pass
