class State:
    """
    For Airbrakes, we will have
    """

    def update(self):
        pass

    def next_state(self):
        """
        We never expect/want to go back a state e.g. We're never going to go
        from Flight to Motor Burn, so this method just goes to the next state.
        """
        pass


class StandByState(State):
    pass

class MotorBurnState(State):
    pass

class FlightState(State):
    pass

class FreeFallState(State):
    pass