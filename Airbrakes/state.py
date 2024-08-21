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
    """"
    On the launch pad
    """
    print("Entered Stand By State")  # Recording State Change
    pass

class MotorBurnState(State):
    """"
    During motor burn
    """
    print("Entered Motor Burn State")  # Recording State Change
    pass

class FlightState(State):
    """
    During free flight
    """
    print("Entered Free Flight State")  # Recording State Change
    pass

class FreeFallState(State):
    """
    During free fall (post apogee)
    """
    print("Entered Free Fall State") # Recording State Change
    pass