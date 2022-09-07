from __future__ import annotations

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
        self.is_on_qdra = False
        self.is_on_qmr = False

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

    def processing(self, session_name: str, path_str: str, p_script_str: str) -> tuple[str, str]:
        self.set_busy()
        stdout, stderr = self.qdra_ssh.exec_sh(session_name=session_name, path=Path(path_str), p_script=Path(p_script_str))
        self.set_not_busy()
        return stdout, stderr

    def get_processing_data(self, session_name: str, path_str: str, delete_flag: bool = False) -> bool:
        self.set_busy()
        path = Path(path_str)
        p_from = path / session_name
        exists = self.qdra_ssh.exists(Path(p_from))
        if not exists:
            return False
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
        return True


settings = read_json_file()
if settings is not None:
    trans_test = TransTest(settings=settings)

router = APIRouter()
router_common = APIRouter()
router_qdra = APIRouter()
router_qmr = APIRouter()
router_test = APIRouter()


@router.get("/hello")
async def trans_hello() -> dict[str, str]:
    return {"Hello": "trans"}


@router_common.get("/makeDir")
async def make_dir(pathStr: str, project: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        path = resolve_path_shared_drives(Path(pathStr))
        if path is None:
            return {"success": False, "error": "Not exist: dir"}
        p_dir = path / project / "auto_test" / "trans" / get_today_string()
        if not p_dir.exists():
            p_dir.mkdir(parents=True)
        trans_test.p_save = p_dir
        return {"success": True, "data": str(p_dir)}

    return wrapper()


@router_qdra.get("/connect")
async def connect_qdra(accessPoint: str) -> dict[str, bool]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool]:
        is_success = check_ping(ip_address=accessPoint)
        if is_success:
            trans_test.is_on_qdra = True
        else:
            trans_test.is_on_qdra = False
        return {"success": True, "isOpen": trans_test.is_on_qdra}

    return wrapper()


@router_qdra.get("/recordStart")
async def qdra_record_start(sessionName: str, duration: int) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qdra_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qdra:
            return {"success": False, "error": "Not open: qDRA"}
        return {"success": trans_test.record_start(session_name=sessionName, duration=duration)}

    return wrapper()


@router_qdra.get("/recordStop")
async def qdra_record_stop() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qdra_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qdra:
            return {"success": False, "error": "Not open: qDRA"}
        return {"success": trans_test.record_stop()}

    return wrapper()


@router_qdra.get("/checkExistence")
async def qdra_check_existence(pathStr: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qdra_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qdra:
            return {"success": False, "error": "Not open: qDRA"}
        exists = trans_test.qdra_ssh.exists(Path(pathStr))
        if exists:
            return {"success": True}
        else:
            return {"success": False, "error": f"Not exist: {pathStr}"}

    return wrapper()


@router_qdra.get("/makeDir")
async def qdra_make_dir(pathStr: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qdra_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qdra:
            return {"success": False, "error": "Not open: qDRA"}
        return {"success": trans_test.qdra_ssh.mkdir(Path(pathStr))}

    return wrapper()


@router_qmr.get("/connect")
async def connect_qmr(accessPoint: str) -> dict[str, bool]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool]:
        is_success = check_ping(ip_address=accessPoint)
        if is_success:
            trans_test.is_on_qmr = True
        else:
            trans_test.is_on_qmr = False
        return {"success": True, "isOpen": trans_test.is_on_qmr}

    return wrapper()


@router_qmr.get("/8psk_2_3")
async def qmr_change_modcod_8psk_2_3() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qmr_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qmr:
            return {"success": False, "error": "Not open: qMR"}
        return {"success": trans_test.change_modcod(modcod=13)}

    return wrapper()


@router_qmr.get("/8psk_5_6")
async def qmr_change_modcod_8psk_5_6() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qmr_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qmr:
            return {"success": False, "error": "Not open: qMR"}
        return {"success": trans_test.change_modcod(modcod=15)}

    return wrapper()


@router_test.get("/processing")
async def processing(sessionName: str, pathStr: str, pathScriptStr: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qdra_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qdra:
            return {"success": False, "error": "Not open: qDRA"}
        stdout, stderr = trans_test.processing(session_name=sessionName, path_str=pathStr, p_script_str=pathScriptStr)
        return {"success": True, "stdout": stdout, "stderr": stderr}

    return wrapper()


@router_test.get("/getProcessingData")
async def get_processing_data(sessionName: str, pathStr: str, deleteFlag: bool = False) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        ip_address = trans_test.qdra_setting.ip_address
        if not check_ping(ip_address) or not trans_test.is_on_qdra:
            return {"success": False, "error": "Not open: qDRA"}
        exists = trans_test.get_processing_data(session_name=sessionName, path_str=pathStr, delete_flag=deleteFlag)
        if exists:
            return {"success": True}
        else:
            return {"success": False, "error": "Processing data not exist"}

    return wrapper()
