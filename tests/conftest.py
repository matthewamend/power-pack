import pytest


def nidaq_present():
    try:
        import nidaqmx
    except ImportError:
        return False

    try:
        devices = list(nidaqmx.system.System.local().devices)
    except nidaqmx.errors.DaqNotSupportedError:
        return False
    except nidaqmx.errors.DaqNotFoundError:
        return False
    except nidaqmx.errors.DaqError:
        return False

    return len(devices) != 0


def pytest_report_header(config):
    """Printed at the top of every run."""
    if nidaq_present():
        return "NI-DAQ device found: running NI-DAQ tests"
    return "No NI-DAQ devices found: skipping NI-DAQ tests"


# --- actually skip the tests (same cached result) --------------------------


def pytest_collection_modifyitems(config, items):
    if nidaq_present():
        return
    skip = pytest.mark.skip(reason="no NI-DAQ device connected")
    for item in items:
        if "nidaq" in item.keywords:
            item.add_marker(skip)
