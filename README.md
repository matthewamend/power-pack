# power-pack

Basic power-pack data collection/manipulation library with some scripts for
measuring power of certain tasks.


## Installation

### With `uv` 

```bash
uv sync

# Run program
uv run power-pack 

# For example:
uv run power-pack "python benchmarks/cpu.py 100"

# Run tests
uv run pytest
```

### With plain-old Python

```bash
# Create venv if you don't already have one
python -m venv .venv
source .venv/bin/activate

pip install -e "."

# For example:
power-pack python benchmarks/cpu.py 100

# Run tests
python -m pytest
```

## Usage

If you are using this as a program:

```bash
power-pack PROGRAM_YOU_WANT_TO_RUN
```

If you are using this as a library:

```python
from power_pack import NIDaqConfig, Acquisition, RunReader

config = NIDaqConfig(2000, 1000, "data.hdf5")

acq = Acquisition(config)

acq.start()

# Run your code here
# ...

acq.stop()

reader = RunReader("data.hdf5")

# Make CSV files
reader.make_csv_files()

# Plot
reader.plot_all()
```

