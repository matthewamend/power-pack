import os

import numpy as np

from power_pack.config import NIDaqConfig
from power_pack.storage import RunReader, RunWriter


def test_writer():
    config = NIDaqConfig(2000, 1000, "test.hdf5")
    w = RunWriter(config)

    for i in range(50):
        arr = np.random.rand(len(config.channel_voltages), 2000)
        w.append(arr)

    w.close()

    r = RunReader("test.hdf5")

    r.make_csv_files()
    r.plot_all()

    r.close()
    os.remove("test.hdf5")
    os.remove("cpu.csv")
    os.remove("disk.csv")
    os.remove("gpu.csv")
    os.remove("motherboard.csv")
