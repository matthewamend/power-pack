from __future__ import annotations

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker

from power_pack.config import NIDaqConfig, channel_voltage_map_by_component


class RunWriter:
    """
    A class that handles writing the samples attained from the NI-DAQ to storage.
    This currently uses `hdf5 <https://www.hdfgroup.org/solutions/hdf5/>`_.

    If you want to read from an hdf5 file holding PowerPack data, use
    :class:`RunReader` instead.

    Note that this is more meant for being used inside the :class:`Acquisition`
    class, not so much by a user.
    """

    def __init__(
        self,
        config: NIDaqConfig,
        chunk_size: int = 2000,
        dtype: np.dtype = np.float32,
    ):
        """
        Initializes a :class:`RunWriter`.

        :param config: The :class:`NIDaqConfig` for the current run. This should
        match the config that is passed to the :class:`Acquisition` instance
        that this writer is going to be used with.

        :param chunk_size: The chunk size of the underlying hdf5 file writer.
        Generally speaking, this really only needs to be tweaked for incredibly
        long runs that last several days.

        :param dtype: The datatype that the samples will be stored as.
        """

        self.f = h5py.File(config.storage_path, "w")

        self.f.attrs["sample_rate"] = config.sample_rate
        self.f.attrs["resistance"] = config.resistance

        self._create_datasets(config, chunk_size, dtype)

    def append(self, arr: np.ndarray) -> None:
        """
        Append data to each channel of data in the current run.

        :param arr: numpy array of shape `(n_channels, n_samples_per_channel)`.
        Each column will be put in the channel corresponding to it, the order of
        the channel being the sames as the order of the channels in the
        `NIDaqConfig.channel_voltages` used to create the `RunWriter`
        """

        if arr.shape[0] != len(self.dsets):
            raise ValueError(
                f"Array data must be 2D with shape ({len(self.dsets)}, n_samples)"
            )

        for col, dset in enumerate(self.dsets):
            old_len = dset.shape[0]
            dset.resize(old_len + arr.shape[1], axis=0)
            dset[old_len:] = arr[col]

    def set_time(self, start: float, end: float) -> None:
        """
        Set the start and end time of the run

        :param start: The starting time, presumably given by :func:`time.time()`
        :param end: The ending time, presumably given by :func:`time.time()`
        """

        self.f.attrs["start_time"] = start
        self.f.attrs["end_time"] = end

    def close(self) -> None:
        """
        Close the connection to the hdf5 file
        """

        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _create_datasets(self, config: NIDaqConfig, chunk_size: int, dtype: np.dtype):
        self.dsets = []

        components = channel_voltage_map_by_component(config.channel_voltages)

        for component, pins in components.items():
            group = self.f.create_group(component)
            for voltage, pin in pins:
                dset = group.create_dataset(
                    pin.replace("/", "_"),  # hdf5 uses "/" as a separator
                    shape=(0,),
                    maxshape=(None,),
                    dtype=dtype,
                    chunks=(chunk_size,),
                    compression="gzip",
                    shuffle=True,
                )
                dset.attrs["voltage"] = voltage.value

                self.dsets.append(dset)


class RunReader:
    """
    A reader that reads an hdf5 file containing info about a run. You can use
    this to create CSV files of the data, graphs of the data, or load the data
    into numpy/pandas to analyze it.
    """

    def __init__(self, path: str):
        """
        Initialize a :class:`RunReader` instance.

        :param path: Path to an hdf5 file with run data already on it.
        """
        self.f = h5py.File(path, "r")
        self.sample_rate = float(self.f.attrs["sample_rate"][()])
        self.resistance = float(self.f.attrs["resistance"][()])

    def dataframe(self, component: str) -> pd.DataFrame:
        """
        Turn the measurements of a particular component into a pandas dataframe

        :param component: The component to turn into a dataframe
        """

        group = self.f[component]

        df = pd.DataFrame()

        for dset_name, dset in group.items():
            if isinstance(dset, h5py.Dataset):
                df[dset_name.replace("_", "/")] = dset[()]

        return df

    def make_csv_files(self, file_prefix: str = "") -> None:
        """
        Create csv files of the pin data for each component. Each component will
        be in a separate CSV file.

        :param file_prefix: The beginning of the file name for each of the
        components' CSV files. All CSVs will be in the form
        "{file_prefix}{component}.csv", e.g. "2026-09-22 18:47:03-cpu.csv"
        or "csv/run28motherboard.csv"
        """
        for component, _ in self._component_groups():
            self.dataframe(component).to_csv(
                f"{file_prefix}{component}.csv",
                index=False,
            )

    def plot_all(
        self,
        file_prefix: str = "",
        power_cap: float | None = None,
        vertical_asymptotes: list[float] | None = None,
        pattern: int = 2,
    ):
        for component, obj in self._component_groups():
            self.plot(component, file_prefix, power_cap, vertical_asymptotes, pattern)

    def plot(
        self,
        component: str,
        file_prefix: str = "",
        power_cap: float | None = None,
        vertical_asymptotes: list[float] | None = None,
        pattern: int = 2,
    ):

        voltage = self.dataframe(component).sum(axis=1).values

        times = np.arange(0, len(voltage)) / self.sample_rate

        window_size = 100

        voltage_windows = np.lib.stride_tricks.sliding_window_view(
            voltage, window_shape=window_size
        )
        time_windows = np.lib.stride_tricks.sliding_window_view(
            times, window_shape=window_size
        )

        voltage_medians = np.median(voltage_windows, axis=1)

        # Use the last time in each window for referencing
        reference_times = time_windows[:, -1]

        plt.rcParams["figure.figsize"] = (16, 6)
        plt.rcParams["figure.dpi"] = 300

        plt.figure()

        plt.plot(
            reference_times,
            voltage_medians,
            label=f"PowerPack Measurements: {component}",
            color="red",
        )

        plt.xlabel("Time (seconds)")
        plt.ylabel("Watts")
        if power_cap is not None:
            plt.title(
                f"{component.title()} Power Consumption Graph (Power Cap = {power_cap} W)"
            )
        else:
            plt.title(f"{component.title()} Power Consumption Graph")

        plt.legend()
        plt.grid(True)
        ax = plt.gca()
        ax.xaxis.set_major_locator(ticker.MultipleLocator(base=2))

        if vertical_asymptotes is not None:
            for count, asymptote in enumerate(vertical_asymptotes):
                color = count % pattern

                rounded_asymptote = round(asymptote, 4)

                if color == 1:
                    value = "b"
                else:
                    value = "g"

                plt.axvline(
                    x=float(asymptote),
                    color=value,
                    label=f"Start time: {rounded_asymptote:.4f}",
                )

        plt.savefig(f"{file_prefix}{component}.png")
        plt.close()

    def close(self) -> None:
        """
        Close the connection to the hdf5 file
        """

        self.f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _component_groups(self):
        for component, obj in self.f.items():
            if isinstance(obj, h5py.Group):
                yield (component, obj)
