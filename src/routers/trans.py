from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from src.common.general import check_ping, get_today_string, resolve_path_shared_drives
from src.engine.qdra import QdraSsh, record_start, record_stop
from src.engine.qmr import ModcodType, change_modcod
from src.engine.read_instrument_settings import InstrumentSetting, read_json_file


class TransTest:
    def __init__(self, settings: InstrumentSetting) -> None:
        self.__is_busy = False
        self.p_save = resolve_path_shared_drives(Path(settings.common.default_path))
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
    path = resolve_path_shared_drives(Path(path_str))
    if path is None:
        return {"success": False, "errorMessage": "Not exist: dir"}
    p_dir = path / "trans" / get_today_string()
    if not p_dir.exists():
        p_dir.mkdir(parents=True)
    trans_test.p_save = p_dir
    return {"success": True, "data": str(p_dir)}


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
