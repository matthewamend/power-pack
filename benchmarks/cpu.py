"""
Simple benchmark that does nothing, then slams the CPU, then does nothing. This
is supposed to simulate a sudden spike.
"""

import sys


def fact(n: int) -> int:
    sum = 1.0
    for i in range(n):
        sum *= n

    return sum


def cpu_burn(n: int) -> int:
    return fact(n * n) * fact(n * n * n) / (n ** (1 / 2))


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} factorial", file=sys.stderr)
    sys.exit(1)

try:
    n = int(sys.argv[1])
except ValueError:
    print(f"Error: argument '{sys.argv[1]}' must be an integer")
    sys.exit(1)

print(cpu_burn(1000))
