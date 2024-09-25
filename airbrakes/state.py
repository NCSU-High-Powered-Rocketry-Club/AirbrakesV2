"""Module for the finite state machine that represents which state of flight we are in."""

from abc import ABC, abstractmethod
import time
from typing import TYPE_CHECKING

from constants import (
    ACCELERATION_AT_MOTOR_BURNOUT,
    APOGEE_SPEED,
    DISTANCE_FROM_APOGEE,
    HIGH_SPEED_AT_MOTOR_BURNOUT,
    MOTOR_BURN_TIME,
    TAKEOFF_HEIGHT,
    TAKEOFF_SPEED,
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
    3. Flight - when the motor has burned out and the rocket is coasting, this is when air brakes will be deployed
    4. Free Fall - when the rocket is falling back to the ground after apogee, this is when the air brakes will be
    retracted
    """

    __slots__ = ("context",)

    def __init__(self, context: "AirbrakesContext"):
        """
        :param context: The state context object that will be used to interact with the electronics
        """
        self.context = context
        # At the very beginning of each state, we retract the airbrakes
        self.context.set_airbrake_extension(0.0)

    @property
    def name(self):
        """
        :return: The name of the state
        """
        return self.__class__.__name__

    @abstractmethod
    def update(self):
        """
        Called every loop iteration. Uses the context to interact with the hardware and decides when to move to the
        next state.
        """

    @abstractmethod
    def next_state(self):
        """
        We never expect/want to go back a state e.g. We're never going to go
        from Flight to Motor Burn, so this method just goes to the next state.
        """


class StandByState(State):
    """
    When the rocket is on the rail on the ground.
    """

    __slots__ = ()

    def update(self):
        """
        Checks if the rocket has launched, based on our speed and altitude.
        """
        # We need to check if the rocket has launched, if it has, we move to the next state.
        # For that we can check:
        # 1) Speed - If the speed of the rocket is above a threshold, the rocket has
        # launched.
        # 2) Altitude - If the altitude is above a threshold, the rocket has launched.
        # Ideally we would directly communicate with the motor, but we don't have that capability.

        data = self.context.data_processor

        if data.speed > TAKEOFF_SPEED or data.current_altitude > TAKEOFF_HEIGHT:
            self.next_state()
            return

    def next_state(self):
        self.context.state = MotorBurnState(self.context)


class MotorBurnState(State):
    """
    When the motor is burning and the rocket is accelerating.
    """

    __slots__ = ("start_time",)

    def __init__(self, context: "AirbrakesContext"):
        super().__init__(context)
        self.start_time = time.time()

    def update(self):
        """Checks to see if the acceleration has dropped to zero, indicating the motor has
        burned out."""

        data = self.context.data_processor

        # If our current speed is less than our max speed, that means we have stopped accelerating
        # This is the same thing as checking if our accel sign has flipped
        if data.speed < data.max_speed:
            self.next_state()
            return
        
        # Fallback: if our motor has burned for longer than its burn time, go to the next state
        if self.start_time - time.time() > MOTOR_BURN_TIME:
            self.next_state()
            return
        

    def next_state(self):
        self.context.state = FlightState(self.context)
        # Deploy the airbrakes as soon as we enter the Flight state
        self.context.set_airbrake_extension(1.0)


class FlightState(State):
    """
    When the motor has burned out and the rocket is coasting to apogee.
    """

    __slots__ = ()

    def update(self):
        """Checks to see if the rocket has reached apogee, indicating the start of free fall."""

        data = self.context.data_processor

        # fallback condition: if our altitude has started to decrease, we have reached apogee:
        if data.max_altitude - data.current_altitude > DISTANCE_FROM_APOGEE:
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
        """Nothing to check, we just wait for the rocket to land."""

    def next_state(self):
        # Explicitly do nothing, there is no next state
        pass
