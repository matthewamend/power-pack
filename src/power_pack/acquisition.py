from __future__ import annotations

import sys
import threading
import time

import nidaqmx
import numpy as np
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
from nidaqmx.stream_readers import AnalogMultiChannelReader

from power_pack.config import NIDaqConfig
from power_pack.storage import RunWriter


class Acquisition:
    """
    A class for running the nidaq collection software to measure power usage
    during a task.

    Typical usage::

        acq = Acquisition("PowerPack task", n_samples_per_callback, sample_rate)
        acq.start()

        # ...

        acq.stop()
    """

    def __init__(self, name: str, config: NIDaqConfig):
        self.config = config
        self.name = name

        self.buffer = np.empty(
            (len(config.channel_voltages), config.n_samples_per_callback),
            dtype=np.float64,
        )

        # Neat little trick where we can preprocess some of the computation.
        # After the voltage is read from the DAQ, we calculate power as
        # (|sample_v| * rail_v) / resistance, so we are precomputing an array
        # with rail_v / resistance for each element, and then we just do abs()
        # and an element-wise multiplication of self.rail_v and our sample array.
        self.rail_v = np.fromiter(
            (
                (float(voltage.value) / 1000) / config.resistance
                for voltage, _ in config.channel_voltages.values()
            ),
            dtype=np.float64,
        )

        # Exception that we can propagate up from the thread if the thread fails
        self._error: BaseException | None = None

        self._ready_event = threading.Event()
        self._ready_timeout = 5.0

        self._stop_event = threading.Event()
        self.started = False
        self.thread: threading.Thread | None = None

    def has_failed(self) -> bool:
        """
        True if the acquisition thread hit an exception.
        """
        return self._error is not None

    def start(self):
        """
        Starts a new acquisition
        """
        if self.started:
            raise RuntimeError("Task already running")

        self._stop_event.clear()
        self._ready_event.clear()
        self._error = None

        self.thread = threading.Thread(target=self._run_task, args=(self._stop_event,))
        self.thread.start()

        if not self._ready_event.wait(self._ready_timeout):
            self.event.set()
            self.thread.join()
            raise TimeoutError(
                f"Measurement '{self.name}' did not start within "
                f"{self._ready_timeout:.0f}s"
            )

        if self._error is not None:
            err, self._error = self._error, None
            raise RuntimeError(f"Measurement '{self.name}' failed to start") from err

        self.start_time = time.time()
        self.started = True

    def stop(self):
        """
        Stops an acquisition
        """
        if not self.started:
            raise RuntimeError("Cannot stop task: there is no task currently running")

        self._stop_event.set()
        self.thread.join()
        self.stop_time = time.time()
        self.total_time = self.stop_time - self.start_time
        self.started = False

        if self._error is not None:
            err, self._error = self._error, None
            raise RuntimeError(
                f"Measurement '{self.name}' failed in DAQ thread"
            ) from err

    def _read_and_append(
        self,
        reader: AnalogMultiChannelReader,
        writer: RunWriter,
        n_samples: int,
    ) -> None:
        if n_samples != self.buffer.shape[1]:
            self.buffer = np.empty((self.buffer.shape[0], n_samples), dtype=np.float64)

        samples_read = reader.read_many_sample(self.buffer, n_samples)

        np.clip(self.buffer, -1e10, 1e10, out=self.buffer)
        np.abs(self.buffer, out=self.buffer)
        self.buffer *= self.rail_v[:, None]

        writer.append(self.buffer[:, :samples_read])

    def _run_task(self, stop_event: threading.Event):
        task = None
        try:
            task = nidaqmx.Task(
                f"Measure {self.name.replace('/', '_').replace('.', '_')} consumption"
            )
            for chan in self.config.channel_voltages:
                task.ai_channels.add_ai_voltage_chan(
                    chan, terminal_config=TerminalConfiguration.DIFF
                )
            task.timing.cfg_samp_clk_timing(
                rate=self.config.sample_rate,
                sample_mode=AcquisitionType.CONTINUOUS,
                samps_per_chan=self.config.n_samples_per_callback,
            )

            reader = AnalogMultiChannelReader(task.in_stream)

            writer = RunWriter(self.config)

            def callback(
                task_handle, every_n_samples_event_type, n_samples, callback_data
            ):
                try:
                    self._read_and_append(reader, writer, n_samples)

                except nidaqmx.errors.DaqError as e:
                    self._error = e
                    print(f"NI-DAQ error in callback: {e}", file=sys.stderr)
                    return -1
                except Exception as ex:
                    self._error = ex
                    print(f"Exception in callback function: {ex}", file=sys.stderr)
                    return -1

                return 0

            task.register_every_n_samples_acquired_into_buffer_event(
                self.config.n_samples_per_callback, callback
            )

            start_time = time.time()
            task.start()
            self._ready_event.set()

            # sleep until stop event
            while not stop_event.wait(0.1):
                if self._error is not None:
                    raise self._error

            end_time = time.time()

            avail = task.in_stream.avail_samp_per_chan
            if avail > 0:
                self._read_and_append(reader, writer, avail)

            writer.set_time(start_time, end_time)

        except nidaqmx.errors.DaqError as e:
            self._error = e
            print(f"NI-DAQ error occurred: {e}", file=sys.stderr)
            raise
        except Exception as ex:
            print(f"Exception occurred in NI-DAQ thread: {ex}", file=sys.stderr)
            self._error = ex
            raise
        finally:
            self._ready_event.set()
            if task is not None:
                task.stop()
                task.close()
