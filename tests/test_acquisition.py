import time

import pytest

from power_pack.acquisition import Acquisition
from power_pack.config import NIDaqConfig

pytestmark = pytest.mark.nidaq


def test_nidaq_connection():
    config = NIDaqConfig(2000, 1000, "test.hdf5")
    acq = Acquisition("Test", config)

    acq.start()

    time.sleep(0.5)

    acq.stop()


def test_nidaq_with_callback():
    config = NIDaqConfig(2000, 1000, "test.hdf5")
    acq = Acquisition("Test", config)

    acq.start()

    time.sleep(2.5)

    acq.stop()
