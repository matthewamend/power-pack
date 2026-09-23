import argparse
import os
import subprocess
import sys
import nidaqmx
from datetime import datetime


from power_pack import Acquisition, NIDaqConfig, RunReader


def parse_args():
    parser = argparse.ArgumentParser(
        prog="PowerPack",
        description="Measure the power utilization of a program",
    )
    parser.add_argument("program")
    parser.add_argument(
        "-s",
        "--sample_rate",
        type=int,
        default=1000,
        help="Number of samples per second to gather",
    )
    parser.add_argument(
        "--n_per_callback",
        type=int,
        default=None,
        help="Number of samples at a time that the NIDaq should give",
    )

    parser.add_argument("rest", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.n_per_callback is None:
        args.n_per_callback = args.sample_rate * 2

    return args


def main():
    args = parse_args()

    now = datetime.now()
    time = now.strftime("%Y-%m-%d %H:%M:%S")

    config = NIDaqConfig(
        args.n_per_callback, args.sample_rate, f"data/{time}-data.hdf5"
    )

    acq = Acquisition(args.program, config)

    os.makedirs("./data", exist_ok=True)
    acq.start()

    subprocess_args = [args.program, *args.rest]
    prog = " ".join(subprocess_args)

    try:
        subprocess.run(subprocess_args, check=True)
    except subprocess.CalledProcessError as cpe:
        print(f"Error: program '{prog}' failed with error code {cpe.returncode}")
        acq.stop()
        sys.exit(cpe.returncode)
    except:
        acq.stop()
        raise

    acq.stop()

    reader = RunReader(f"data/{time}-data.hdf5")
    reader.make_csv_files(f"data/{time}-")
    reader.plot_all(f"data/{time}-")

    sys.exit(0)


if __name__ == "__main__":
    main()
