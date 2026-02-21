import timeit

setup_1 = """

import msgspec


class TestPacket(msgspec.Struct, tag=True, array_like=True):
    a: int
    b: int
    c: int
    d: int
"""

test_1 = """

packet = TestPacket(a=10, b=3, c=5, d=7)
"""

setup_2 = """
import msgspec

class TestPacket(msgspec.Struct, tag=True, array_like=True, frozen=True):
    a: int
    b: int
    c: int
    d: int
"""

test_2 = """
packet = TestPacket(a=10, b=3, c=5, d=7)
"""

test_1 = timeit.timeit(test_1, setup=setup_1, number=1_000_000)
print(f"Test 1 (4 fields): {test_1}")

test_2 = timeit.timeit(test_2, setup=setup_2, number=1_000_000)
print(f"Test 2 (4 fields, frozen): {test_2}") 