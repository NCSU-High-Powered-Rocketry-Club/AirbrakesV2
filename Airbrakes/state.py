from Airbrakes.airbrakes import AirbrakesContext


class State:
    """
    For Airbrakes, we will have 4 states:
    1. Stand By - when the rocket is on the rail on the ground
    2. Motor Burn - when the motor is burning and the rocket is accelerating
    3. Flight - when the motor has burned out and the rocket is coasting, this is when air brakes will be deployed
    4. Free Fall - when the rocket is falling back to the ground after apogee, this is when the air brakes will be
    retracted
    """

    __slots__ = ("context",)

    def __init__(self, context: AirbrakesContext):
        """
        :param context: The state context object that will be used to interact with the electronics
        """
        self.context = context
        # At the very beginning of each state, we retract the airbrakes
        self.context.set_airbrake_extension(0.0)

    def update(self):
        """
        Called every loop iteration. Uses the context to interact with the hardware and decides when to move to the
        next state.
        """
        pass

    def next_state(self):
        """
        We never expect/want to go back a state e.g. We're never going to go
        from Flight to Motor Burn, so this method just goes to the next state.
        """
        pass

    def get_name(self):
        """
        :return: The name of the state
        """
        return self.__class__.__name__


class StandByState(State):
    """
    When the rocket is on the rail on the ground.
    """

    __slots__ = ()

    def update(self):
        pass

    def next_state(self):
        self.context.state = MotorBurnState(self.context)


class MotorBurnState(State):
    """
    When the motor is burning and the rocket is accelerating.
    """

    __slots__ = ()

    def update(self):
        pass

    def next_state(self):
        self.context.state = FlightState(self.context)


class FlightState(State):
    """
    When the motor has burned out and the rocket is coasting.
    """

    __slots__ = ()

    def update(self):
        pass

    def next_state(self):
        self.context.state = FreeFallState(self.context)


class FreeFallState(State):
    """
    When the rocket is falling back to the ground after apogee.
    """

    __slots__ = ()

    def update(self):
        pass

    def next_state(self):
        # Explicitly do nothing, there is no next state
        pass
