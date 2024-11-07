import timeit
import yaml
from pathlib import Path
import random
import numpy as np

config_path = Path("simulator/sim_config.yaml")
with config_path.open(mode="r", newline="") as file:
    config: dict = yaml.safe_load(file)
rng = np.random.default_rng()
# Define the two functions to test
def function1():
    a = rng.random()

def function2():
    a = random.random()

# Number of executions for each function (increase for more precise timing)
num_executions = 10

# Time the execution of function1
time_function1 = timeit.timeit("function1()", globals=globals(), number=num_executions)

# Time the execution of function2
time_function2 = timeit.timeit("function2()", globals=globals(), number=num_executions)

# Print the results
print(f"Time taken by function1: {time_function1:.6f} seconds")
print(f"Time taken by function2: {time_function2:.6f} seconds")

# Compare which function is faster
if time_function1 < time_function2:
    print("function1 is faster")
elif time_function1 > time_function2:
    print("function2 is faster")
else:
    print("Both functions have the same execution time")






