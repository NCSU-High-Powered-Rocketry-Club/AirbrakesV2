import random
import timeit
from pathlib import Path

import numpy as np
import yaml

config_path = Path("simulation/sim_config.yaml")
with config_path.open(mode="r", newline="") as file:
    config: dict = yaml.safe_load(file)
rng = np.random.default_rng()


# Define the two functions to test
def function1():
    rng.random()


def function2():
    random.random()


# Number of executions for each function (increase for more precise timing)
num_executions = 10

# Time the execution of function1
time_function1 = timeit.timeit("function1()", globals=globals(), number=num_executions)

# Time the execution of function2
time_function2 = timeit.timeit("function2()", globals=globals(), number=num_executions)

# Print the results

# Compare which function is faster
if time_function1 < time_function2 or time_function1 > time_function2:
    pass
else:
    pass
