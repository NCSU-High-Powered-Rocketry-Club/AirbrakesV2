import queue
import timeit
import threading


msgspec_setup = """
import msgspec

class TestPacket(msgspec.Struct):
    value: float
    val_2: int

"""

setup_1 = f"""
import queue
{msgspec_setup}

q = queue.Queue()
"""

setup_2 = f"""
import queue
{msgspec_setup}

q = queue.SimpleQueue()
"""


stmt_put = """
q.put(1)
"""

stmt_msgspec_put = """
packet = TestPacket(value=1.0, val_2=2)
q.put(packet)
"""

time_1 = timeit.timeit(stmt_put, setup=setup_1, number=1)
time_2 = timeit.timeit(stmt_put, setup=setup_2, number=1)

print(f"queue.Queue put time: {time_1 * 1e6:.8f} us")
print(f"queue.SimpleQueue put time: {time_2 * 1e6:.8f} us")

time_3 = timeit.timeit(stmt_msgspec_put, setup=setup_1, number=1000000)
time_4 = timeit.timeit(stmt_msgspec_put, setup=setup_2, number=1000000)
print(f"queue.Queue msgspec put time: {time_3:.6f} seconds")
print(f"queue.SimpleQueue msgspec put time: {time_4:.6f} seconds")


add_to_queue = """
for _ in range(100000):
    q.put(1)
"""
setup_3 = setup_1 + add_to_queue
setup_4 = setup_2 + add_to_queue

stmt_get = """
while not q.empty():
    q.get()
"""

time_5 = timeit.timeit(stmt_get, setup=setup_3, number=1)
time_6 = timeit.timeit(stmt_get, setup=setup_4, number=1)
print(f"queue.Queue get time: {time_5:.6f} seconds")
print(f"queue.SimpleQueue get time: {time_6:.6f} seconds")



