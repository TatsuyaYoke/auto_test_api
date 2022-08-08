from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, error_wrappers

if getattr(sys, "frozen", False):
    p_this_file = Path(sys.executable)
    p_top = p_this_file.resolve().parent
else:
    p_this_file = Path(__file__)
    p_top = p_this_file.resolve().parent.parent.parent

P_SETTING = p_top / ".settings/settings.json"


class NetworkSetting(BaseModel):
    ip_address: str
    port: int
    ssh_port: Optional[int]
    username: Optional[str]
    password: Optional[str]


class VisaSetting(NetworkSetting):
    pass


class Gl840Setting(BaseModel):
    visa: VisaSetting


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


class InstrumentSetting(BaseModel):
    gl840: Gl840Setting
    sas: SasSetting
    bus: BusJigSetting
    qmr: QmrSetting
    qdra: QdraSetting


def read_json_file() -> Optional[InstrumentSetting]:
    try:
        json_load = InstrumentSetting.parse_file(P_SETTING)
    except error_wrappers.ValidationError:
        json_load = None
    return json_load


if __name__ == "__main__":
    print(read_json_file())
