from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from src.common import general
from src.common.general import get_today_string
from src.engine.power_sensor import PowerSensor
from src.engine.read_instrument_settings import read_json_file
from src.engine.signal_analyzer import FreqResponse, SignalAnalyzer


class ObsTest:
    def __init__(self, p_save: Path) -> None:
        self.p_save = p_save


settings = read_json_file()
if settings is not None:
    power_sensor_address = settings.power_sensor.visa
    power_sensor = PowerSensor(address=power_sensor_address)

    signal_analyzer_address = settings.signal_analyzer.visa
    p_capture = Path(settings.signal_analyzer.capture_path)
    signal_analyzer = SignalAnalyzer(address=signal_analyzer_address, p_capture=p_capture)

    p_save = Path(settings.common.default_path)
    obs_test = ObsTest(p_save=p_save)

router = APIRouter()


@router.get("/hello")
async def obs_hello() -> dict[str, str]:
    return {"Hello": "obs"}


@router.get("/makeDir")
async def make_dir(path_str: str) -> dict[str, bool | str]:
    path = Path(path_str)
    if not path.exists():
        return {"success": False, "errorMessage": "Specified path not exist"}
    p_dir = path / "obs" / get_today_string()
    if not p_dir.exists():
        p_dir.mkdir(parents=True)
    obs_test.p_save = p_dir
    return {"success": True, "path": str(p_dir)}


@router.get("/connectPowerSensor")
async def connect_power_sensor() -> dict[str, bool]:
    return {"isOpen": power_sensor.connect()}


@router.get("/getSingleDataPowerSensor")
async def get_single_data_power_sensor() -> dict[str, bool | str | float]:
    is_open = power_sensor.get_open_status()

    if not is_open:
        return {"success": False, "errorMessage": "not open"}
    data = power_sensor.get_data()
    if data is None:
        return {"success": False, "errorMessage": "Data is None"}
    return {"success": True, "data": data}


@router.get("/connectSignalAnalyzer")
async def connect_signal_analyzer() -> dict[str, bool]:
    return {"isOpen": signal_analyzer.connect()}


@router.get("/restartSignalAnalyzer")
async def restart_signal_analyzer() -> dict[str, bool | str]:

    try:
        signal_analyzer.send_restart_command()
        return {"success": True}
    except Exception as error:
        return {"success": False, "errorMessage": str(error)}


@router.get("/getTraceSignalAnalyzer")
async def get_trace_signal_analyzer() -> dict[str, bool | str | FreqResponse]:

    is_open = signal_analyzer.get_open_status()
    if not is_open:
        {"success": False, "errorMessage": "not open"}
    data = signal_analyzer.get_data(trace_num=1)
    if data is None:
        return {"success": False, "errorMessage": "Data is None"}
    return {"success": True, "data": data}


@router.get("/getCaptureSignalAnalyzer")
async def get_capture_signal_analyzer() -> dict[str, bool | str | list[int | float]]:

    is_open = signal_analyzer.get_open_status()
    if not is_open:
        {"success": False, "errorMessage": "not open"}
    data = signal_analyzer.get_capture(picture_name="capture_test", deletes_picture=True)
    if data is None:
        return {"success": False, "errorMessage": "Data is None"}

    path = obs_test.p_save / "capture.png"
    general.save_picture_from_binary_list(data=data, path=path)
    return {"success": True, "path": str(path)}
