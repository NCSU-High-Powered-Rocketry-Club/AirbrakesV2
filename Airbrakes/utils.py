import time


def run_at_frequency(func: object, frequency: int) -> None:
    """
    Runs func every 
    :param:`frequency` seconds.
    """
    start_time = time.time()

    # Update the airbrakes system
    func()

    # Calculate the time taken by the update method
    elapsed_time = time.time() - start_time

    # Sleep for the remaining time to maintain 100 Hz frequency
    time_to_sleep = max(0, 1 / frequency - elapsed_time)

    if 1 / frequency - elapsed_time < 0:
        print("Loop Overrun")

    time.sleep(time_to_sleep)
