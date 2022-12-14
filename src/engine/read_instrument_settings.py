from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, error_wrappers

if getattr(sys, "frozen", False):
    p_this_file = Path(sys.executable)
    p_top = p_this_file.resolve().parent
else:
    p_this_file = Path(__file__)
    p_top = p_this_file.resolve().parent.parent.parent

P_SETTING = p_top / ".settings/settings.json"


class CommonSetting(BaseModel):
    default_path: str


class TransSetting(BaseModel):
    ignore_file_extension: List[str]
    ignore_file: List[str]


class NetworkSetting(BaseModel):
    ip_address: str
    port: int


class SshSetting(NetworkSetting):
    username: str
    password: str


class Gl840Setting(BaseModel):
    visa: str
    ftp: NetworkSetting


class SerialSetting(BaseModel):
    port: str
    baudrate: int = 9600
    parity: str = "N"


class SasOutputSetting(BaseModel):
    voc: float = 50
    isc: float = 0.1
    fill_factor: float = 0.9


class SasRepeatSetting(BaseModel):
    orbit_period: int = 90 * 60
    sun_rate: float = 0.6
    offset: int = 0
    interval: int = 1


class SasSetting(BaseModel):
    serial: SerialSetting
    output: SasOutputSetting
    repeat: SasRepeatSetting


class BusJigSetting(BaseModel):
    serial: SerialSetting


class QmrSetting(BaseModel):
    network: NetworkSetting


class QdraSetting(BaseModel):
    network: NetworkSetting
    ssh: SshSetting


class PowerSensorSetting(BaseModel):
    visa: str


class SignalAnalyzerSetting(BaseModel):
    visa: str
    capture_path: str


class InstrumentSetting(BaseModel):
    common: CommonSetting
    trans: TransSetting
    gl840: Gl840Setting
    sas: SasSetting
    bus_jig: BusJigSetting
    qmr: QmrSetting
    qdra: QdraSetting
    power_sensor: PowerSensorSetting
    signal_analyzer: SignalAnalyzerSetting


def read_json_file() -> Optional[InstrumentSetting]:
    try:
        json_load = InstrumentSetting.parse_file(P_SETTING)
    except error_wrappers.ValidationError:
        json_load = None
    return json_load


if __name__ == "__main__":
    print(read_json_file())
