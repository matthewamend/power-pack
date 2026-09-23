from dataclasses import dataclass
from enum import Enum


class Voltage(Enum):
    V_3_3 = 3300
    V_5 = 5000
    V_12 = 12000


CHANNEL_VOLTAGE_MAP = {
    "cDAQ2Mod8/ai0": (Voltage.V_3_3, "motherboard"),
    "cDAQ2Mod8/ai1": (Voltage.V_3_3, "motherboard"),
    "cDAQ2Mod8/ai2": (Voltage.V_3_3, "motherboard"),
    "cDAQ2Mod8/ai3": (Voltage.V_3_3, "motherboard"),
    "cDAQ2Mod6/ai0": (Voltage.V_5, "motherboard"),
    "cDAQ2Mod6/ai1": (Voltage.V_5, "motherboard"),
    "cDAQ2Mod6/ai2": (Voltage.V_5, "motherboard"),
    "cDAQ2Mod6/ai3": (Voltage.V_5, "motherboard"),
    "cDAQ2Mod6/ai4": (Voltage.V_5, "motherboard"),
    "cDAQ2Mod2/ai17": (Voltage.V_12, "motherboard"),
    "cDAQ2Mod2/ai18": (Voltage.V_12, "motherboard"),
    "cDAQ2Mod2/ai19": (Voltage.V_12, "motherboard"),
    "cDAQ2Mod2/ai4": (Voltage.V_12, "cpu"),
    "cDAQ2Mod2/ai5": (Voltage.V_12, "cpu"),
    "cDAQ2Mod2/ai6": (Voltage.V_12, "cpu"),
    "cDAQ2Mod2/ai7": (Voltage.V_12, "cpu"),
    "cDAQ2Mod2/ai0": (Voltage.V_12, "gpu"),
    "cDAQ2Mod2/ai1": (Voltage.V_12, "gpu"),
    "cDAQ2Mod2/ai2": (Voltage.V_12, "gpu"),
    "cDAQ2Mod2/ai3": (Voltage.V_12, "gpu"),
    "cDAQ2Mod8/ai7": (Voltage.V_3_3, "disk"),
    "cDAQ2Mod6/ai7": (Voltage.V_5, "disk"),
    "cDAQ2Mod2/ai23": (Voltage.V_12, "disk"),
}


def channel_voltage_map_by_component(
    map: dict[str, tuple[Voltage, str]],
) -> dict[str, tuple[Voltage, str]]:
    components = {}
    for pin, (voltage, component) in map.items():
        if component in components:
            components[component].append((voltage, pin))
        else:
            components[component] = [(voltage, pin)]

    return components


@dataclass
class NIDaqConfig:
    n_samples_per_callback: int
    sample_rate: int
    storage_path: str
    channel_voltages: dict[str, tuple[Voltage, str]]
    resistance: int = 0.003

    def __init__(
        self,
        n_samples_per_callback: int,
        sample_rate: int,
        storage_path: str,
        channel_voltages: dict[str, tuple[Voltage, str]] = CHANNEL_VOLTAGE_MAP,
        resistance: int = 0.003,
    ):
        self.n_samples_per_callback = n_samples_per_callback
        self.sample_rate = sample_rate
        self.storage_path = storage_path
        self.channel_voltages = channel_voltages
        self.resistance = resistance
