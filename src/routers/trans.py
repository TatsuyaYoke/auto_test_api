from __future__ import annotations

import threading
from pathlib import Path

from fastapi import APIRouter

import src.common.settings
from src.common.decorator import exception
from src.common.general import check_ping, get_today_string, resolve_path_shared_drives
from src.common.logger import set_logger
from src.engine.qdra import QdraSsh, record_start, record_stop
from src.engine.qmr import ModcodType, change_modcod
from src.engine.read_instrument_settings import InstrumentSetting, read_json_file

LOGGER_IS_ACTIVE_STREAM = src.common.settings.logger_is_active_stream
logger = set_logger(__name__, is_active_stream=LOGGER_IS_ACTIVE_STREAM)


class TransTest:
    def __init__(self, settings: InstrumentSetting) -> None:
        self.__is_busy = False
        self.p_save = resolve_path_shared_drives(Path(settings.common.default_path))
        self.trans_setting = settings.trans
        self.qdra_setting = settings.qdra.network
        self.qmr_setting = settings.qmr.network

        qdra_ssh_setting = settings.qdra.ssh
        self.qdra_ssh = QdraSsh(
            host=qdra_ssh_setting.ip_address, port=qdra_ssh_setting.port, username=qdra_ssh_setting.username, password=qdra_ssh_setting.password
        )

    def set_busy(self) -> None:
        self.__is_busy = True

    def set_not_busy(self) -> None:
        self.__is_busy = False

    def get_busy_status(self) -> bool:
        return self.__is_busy

    def change_modcod(self, modcod: ModcodType) -> bool:
        ip_address = self.qmr_setting.ip_address
        port = self.qmr_setting.port
        response = change_modcod(ip_address=ip_address, port=port, modcod=modcod)

        if response == 200:
            return True
        else:
            return False

    def record_start(self, session_name: str, duration: int) -> bool:
        ip_address = self.qdra_setting.ip_address
        port = self.qdra_setting.port
        session_desc = ""
        response = record_start(ip_address=ip_address, port=port, session_name=session_name, session_desc=session_desc, duration=duration)

        if response == 200:
            return True
        else:
            return False

    def record_stop(self) -> bool:
        ip_address = self.qdra_setting.ip_address
        port = self.qdra_setting.port
        response = record_stop(ip_address=ip_address, port=port)

        if response == 200:
            return True
        else:
            return False

    def processing(self, session_name: str, path_str: str, p_script_str: str) -> None:
        self.set_busy()
        self.qdra_ssh.exec_sh(session_name=session_name, path=Path(path_str), p_script=Path(p_script_str))
        self.set_not_busy()

    def get_processing_data(self, session_name: str, path_str: str, delete_flag: bool = False) -> None:
        self.set_busy()
        path = Path(path_str)
        p_from = path / session_name
        file_list = self.qdra_ssh.get_list_dir(path=p_from)

        if self.p_save is not None:
            p_to = self.p_save / session_name
            if not p_to.exists():
                p_to.mkdir(parents=True)
            for f in file_list:
                self.qdra_ssh.get_file(p_server=p_from / f, p_save=p_to / f)
        if delete_flag:
            self.qdra_ssh.delete_dir(p_from)

        self.set_not_busy()


settings = read_json_file()
if settings is not None:
    trans_test = TransTest(settings=settings)

router = APIRouter()
router_common = APIRouter()
router_qdra = APIRouter()
router_qmr = APIRouter()
router_test = APIRouter()


@router.get("/hello")
async def obs_hello() -> dict[str, str]:
    return {"Hello": "trans"}


@router_common.get("/makeDir")
async def make_dir(path_str: str) -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        path = resolve_path_shared_drives(Path(path_str))
        if path is None:
            return {"success": False, "error": "Not exist: dir"}
        p_dir = path / "trans" / get_today_string()
        if not p_dir.exists():
            p_dir.mkdir(parents=True)
        trans_test.p_save = p_dir
        return {"success": True, "data": str(p_dir)}

    return wrapper()


@router_qdra.get("/connect")
async def connect_qdra() -> dict[str, bool]:
    ip_address = trans_test.qdra_setting.ip_address
    return {"isOpen": check_ping(ip_address)}


@router_qdra.get("/recordStart")
async def qdra_record_start(session_name: str, duration: int) -> dict[str, bool]:
    return {"success": trans_test.record_start(session_name=session_name, duration=duration)}


@router_qdra.get("/recordStop")
async def qdra_record_stop() -> dict[str, bool]:
    return {"success": trans_test.record_stop()}


@router_qdra.get("/checkExistence")
async def qdra_check_existence(path_str: str) -> dict[str, bool | str]:
    ip_address = trans_test.qdra_setting.ip_address
    if not check_ping(ip_address):
        return {"success": False, "error": "Not open: qDRA"}
    exists = trans_test.qdra_ssh.exists(Path(path_str))
    if exists:
        return {"success": True}
    else:
        return {"success": False, "error": f"Not exist: {path_str}"}


@router_qdra.get("/makeDir")
async def qdra_make_dir(path_str: str) -> dict[str, bool | str]:
    ip_address = trans_test.qdra_setting.ip_address
    if not check_ping(ip_address):
        return {"success": False, "error": "Not open: qDRA"}
    return {"success": trans_test.qdra_ssh.mkdir(Path(path_str))}


@router_qmr.get("/connect")
async def connect_qmr() -> dict[str, bool]:
    ip_address = trans_test.qmr_setting.ip_address
    return {"isOpen": check_ping(ip_address)}


@router_qmr.get("/8psk_2_3")
async def qmr_change_modcod_8psk_2_3() -> dict[str, bool]:
    return {"success": trans_test.change_modcod(modcod=13)}


@router_qmr.get("/8psk_5_6")
async def qmr_change_modcod_8psk_5_6() -> dict[str, bool]:
    return {"success": trans_test.change_modcod(modcod=15)}


@router_test.get("/processing")
async def processing(session_name: str, path_str: str, p_script_str: str) -> dict[str, bool | str]:
    ip_address = trans_test.qdra_setting.ip_address
    if not check_ping(ip_address):
        return {"success": False, "error": "Not open: qDRA"}
    t = threading.Thread(target=trans_test.processing, args=[session_name, path_str, p_script_str])
    t.start()
    return {"success": True}


@router_test.get("/getProcessingData")
async def get_processing_data(session_name: str, path_str: str, delete_flag: bool = False) -> dict[str, bool | str]:
    ip_address = trans_test.qdra_setting.ip_address
    if not check_ping(ip_address):
        return {"success": False, "error": "Not open: qDRA"}
    t = threading.Thread(target=trans_test.get_processing_data, args=[session_name, path_str, delete_flag])
    t.start()
    return {"success": True}
