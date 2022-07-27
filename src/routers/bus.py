from __future__ import annotations

from fastapi import APIRouter

from src.engine.bus_jig import BusJigSerial
from src.engine.read_instrument_settings import read_json_file

router = APIRouter()


BUS_JIG_SERIAL = BusJigSerial()
SETTING = read_json_file()
if SETTING is not None:
    BUS_SETTING = SETTING.bus
    PORT = BUS_SETTING.serial.port
    BAUDRATE = BUS_SETTING.serial.baudrate
    PARITY = BUS_SETTING.serial.parity


@router.get("/bus_jig_connect")
async def bus_jig_connect() -> dict[str, bool]:

    BUS_JIG_SERIAL.set_port(port=PORT, baudrate=BAUDRATE, parity=PARITY)
    port_status = BUS_JIG_SERIAL.get_port_status()
    return {"success": port_status}


@router.get("/bus_jig_disconnect")
async def bus_jig_disconnect() -> dict[str, bool]:

    BUS_JIG_SERIAL.close_port()
    port_status = BUS_JIG_SERIAL.get_port_status()
    return {"success": not port_status}


@router.get("/sat_ena")
async def sat_ena() -> dict[str, bool]:

    if BUS_JIG_SERIAL.get_port_status():
        BUS_JIG_SERIAL.send_sat_ena()
        return {"success": True}
    else:
        return {"success": False}


@router.get("/sat_dis")
async def sat_dis() -> dict[str, bool]:

    if BUS_JIG_SERIAL.get_port_status():
        BUS_JIG_SERIAL.send_sat_dis()
        return {"success": True}
    else:
        return {"success": False}
