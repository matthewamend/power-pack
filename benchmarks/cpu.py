"""
Simple benchmark that does nothing, then slams the CPU, then does nothing. This
is supposed to simulate a sudden spike.
"""

import math
import time

from power_pack import Acquisition, NIDaqConfig, RunReader


def cpu_burn(n: int) -> float:
    x = math.factorial(n * n)
    y = math.factorial(n * n * int(math.sqrt(n)))

    return x * y


if __name__ == "__main__":
    n = 10

    config = NIDaqConfig(2000, 1000, "cpu_burn.hdf5")

    acq = Acquisition("Example CPU utilization benchmark", config)

    acq.start()

    for i in range(10):
        for _ in range(1000):
            cpu_burn(n + i)
        time.sleep(0.2)

    acq.stop()

    reader = RunReader("cpu_burn.hdf5")

    reader.make_csv_files()

    reader.plot_all()
