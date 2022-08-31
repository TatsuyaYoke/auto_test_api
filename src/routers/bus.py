from __future__ import annotations

from fastapi import APIRouter

import src.common.settings
from src.common.decorator import exception
from src.common.logger import set_logger
from src.engine.bus_jig import BusJigSerial
from src.engine.gl840 import Gl840Visa
from src.engine.read_instrument_settings import (
    InstrumentSetting,
    SasOutputSetting,
    SasRepeatSetting,
    read_json_file,
)
from src.engine.sas import SasSerial

LOGGER_IS_ACTIVE_STREAM = src.common.settings.logger_is_active_stream
logger = set_logger(__name__, is_active_stream=LOGGER_IS_ACTIVE_STREAM)


class BusTest:
    def __init__(self, settings: InstrumentSetting) -> None:

        self.bus_jig_setting = settings.bus_jig.serial
        self.bus_jig = BusJigSerial()

        self.gl840_setting = settings.gl840.visa
        self.gl840 = Gl840Visa()

        self.sas_setting = settings.sas.serial
        self.sas = SasSerial()


settings = read_json_file()
if settings is not None:
    bus_test = BusTest(settings=settings)

router = APIRouter()
router_bus_jig = APIRouter()
router_sas = APIRouter()
router_gl840 = APIRouter()


@router.get("/hello")
async def bus_hello() -> dict[str, str]:
    return {"Hello": "bus"}


@router_bus_jig.get("/connect")
async def bus_jig_connect(accessPoint: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        baudrate = bus_test.bus_jig_setting.baudrate
        parity = bus_test.bus_jig_setting.parity
        is_success = bus_test.bus_jig.set_port(port=accessPoint.upper(), baudrate=baudrate, parity=parity)
        if is_success:
            return {"success": True, "isOpen": bus_test.bus_jig.get_port_status()}
        else:
            return {"success": False, "error": "Port name is not correct or please close port"}

    return wrapper()


@router_bus_jig.get("/disconnect")
async def bus_jig_disconnect() -> dict[str, bool]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.bus_jig.close_port()
        return {"success": True, "isOpen": bus_test.bus_jig.get_port_status()}

    return wrapper()


@router_bus_jig.get("/sat_ena")
async def sat_ena() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        is_open = bus_test.bus_jig.get_port_status()
        if not is_open:
            return {"success": False, "error": "Not open: bus jig"}
        bus_test.bus_jig.send_sat_ena()
        return {"success": True}

    return wrapper()


@router_bus_jig.get("/sat_dis")
async def sat_dis() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        is_open = bus_test.bus_jig.get_port_status()
        if not is_open:
            return {"success": False, "error": "Not open: bus jig"}
        bus_test.bus_jig.send_sat_dis()
        return {"success": True}

    return wrapper()


@router_gl840.get("/connect")
async def gl840_connect(accessPoint: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.gl840.connect(address=accessPoint)
        return {"success": True, "isOpen": bus_test.gl840.get_open_status()}

    return wrapper()


@router_gl840.get("/disconnect")
async def gl840_disconnect() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.gl840.close_resource()
        return {"success": True, "isOpen": bus_test.gl840.get_open_status()}

    return wrapper()


@router_gl840.get("/recordStart")
async def gl840_record_start() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.gl840.record_start()
        return {"success": True}

    return wrapper()


@router_gl840.get("/recordStop")
async def gl840_record_stop() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.gl840.record_stop()
        return {"success": True}

    return wrapper()


@router_sas.get("/connect")
async def sas_connect(accessPoint: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        baudrate = bus_test.sas_setting.baudrate
        parity = bus_test.sas_setting.parity
        is_success = bus_test.sas.set_port(port=accessPoint.upper(), baudrate=baudrate, parity=parity)
        if is_success:
            return {"success": True, "isOpen": bus_test.sas.get_port_status()}
        else:
            return {"success": False, "error": "Port name is not correct or please close port"}

    return wrapper()


@router_sas.get("/disconnect")
async def sas_disconnect() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.sas.close_port()
        return {"success": True, "isOpen": bus_test.sas.get_port_status()}

    return wrapper()


@router_sas.get("/on")
async def sas_on(voc: float, isc: float, fill_factor: float) -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        setting = SasOutputSetting(voc=voc, isc=isc, fill_factor=fill_factor)
        bus_test.sas.output(onoff="on", setting=setting)
        return {"success": bus_test.sas.get_output_status()}

    return wrapper()


@router_sas.get("/off")
async def sas_off() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.sas.output("off")
        return {"success": not bus_test.sas.get_output_status()}

    return wrapper()


@router_sas.get("/repeatOn")
async def sas_repeat_on(voc: float, isc: float, fill_factor: float, orbit_period: int, sun_rate: float, offset: int) -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        output_setting = SasOutputSetting(voc=voc, isc=isc, fill_factor=fill_factor)
        repeat_setting = SasRepeatSetting(orbit_period=orbit_period, sun_rate=sun_rate, offset=offset, interval=1)
        bus_test.sas.repeat_on(output_setting=output_setting, repeat_setting=repeat_setting)
        return {"success": bus_test.sas.get_repeat_status()}

    return wrapper()


@router_sas.get("/repeatOff")
async def sas_repeat_off() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        bus_test.sas.repeat_off()
        return {"success": bus_test.sas.get_repeat_status()}

    return wrapper()
