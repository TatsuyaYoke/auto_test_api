from __future__ import annotations

import threading
from pathlib import Path
from time import perf_counter, sleep

from fastapi import APIRouter

from src.common import general
from src.common.general import get_today_string, resolve_path_shared_drives
from src.engine.power_sensor import PowerSensor
from src.engine.read_instrument_settings import InstrumentSetting, read_json_file
from src.engine.signal_analyzer import FreqResponse, SignalAnalyzer


class ObsTest:
    def __init__(self, settings: InstrumentSetting) -> None:
        self.__is_busy = False
        self.p_save = resolve_path_shared_drives(Path(settings.common.default_path))

        power_sensor_address = settings.power_sensor.visa
        self.power_sensor = PowerSensor(address=power_sensor_address)

        signal_analyzer_address = settings.signal_analyzer.visa
        p_capture = Path(settings.signal_analyzer.capture_path)
        self.signal_analyzer = SignalAnalyzer(address=signal_analyzer_address, p_capture=p_capture)

    def set_busy(self) -> None:
        self.__is_busy = True

    def set_not_busy(self) -> None:
        self.__is_busy = False

    def get_busy_status(self) -> bool:
        return self.__is_busy

    def get_chirp_before_obs(self, test_name: str, duration: int) -> None:
        self.set_busy()

        if self.p_save is not None:
            p_dir = self.p_save / test_name
            if not p_dir.exists():
                p_dir.mkdir()

            for test_num in range(duration):
                picture_name = f"before_obs_{test_num}"
                filename = f"{picture_name}.png"
                path = p_dir / filename
                data = self.signal_analyzer.get_capture(picture_name=picture_name, deletes_picture=True)
                if data is not None:
                    general.save_picture_from_binary_list(data=data, path=path)
                if not self.get_busy_status():
                    break
                sleep(1)
        self.set_not_busy()

    def get_obs_data(self, test_name: str, wait_sec: int) -> None:
        self.set_busy()
        interval = 0.1
        elapsed_time = 0.0
        time_start = perf_counter()
        time_list: list[float] = []
        power_list: list[float] = []

        if self.p_save is not None:
            p_dir = self.p_save / test_name
            if not p_dir.exists():
                p_dir.mkdir()

            self.signal_analyzer.send_restart_command()

            while elapsed_time <= wait_sec:
                sleep(interval)
                elapsed_time = perf_counter() - time_start
                data = self.power_sensor.get_data()
                if data is not None:
                    time_list.append(elapsed_time)
                    power_list.append(data)

            filename_stem = "obs"
            p_png = p_dir / f"{filename_stem}.png"
            p_csv = p_dir / f"{filename_stem}.csv"

            capture = self.signal_analyzer.get_capture(picture_name=filename_stem, deletes_picture=True)
            if capture is not None:
                general.save_picture_from_binary_list(data=capture, path=p_png)

            dict_data = {"time": time_list, "power": power_list}
            general.save_csv_from_dict(data=dict_data, path=p_csv)

        self.set_not_busy()


settings = read_json_file()
if settings is not None:
    obs_test = ObsTest(settings=settings)

router = APIRouter()
router_common = APIRouter()
router_power_sensor = APIRouter()
router_signal_analyzer = APIRouter()
router_test = APIRouter()


@router.get("/hello")
async def obs_hello() -> dict[str, str]:
    return {"Hello": "obs"}


@router_common.get("/makeDir")
async def make_dir(path_str: str) -> dict[str, bool | str]:
    path = resolve_path_shared_drives(Path(path_str))
    if path is None:
        return {"success": False, "errorMessage": "Not exist: dir"}
    p_dir = path / "obs" / get_today_string()
    if not p_dir.exists():
        p_dir.mkdir(parents=True)
    obs_test.p_save = p_dir
    return {"success": True, "data": str(p_dir)}


@router_power_sensor.get("/connect")
async def connect_power_sensor() -> dict[str, bool]:
    return {"isOpen": obs_test.power_sensor.connect()}


@router_power_sensor.get("/disconnect")
async def disconnect_power_sensor() -> dict[str, bool]:
    obs_test.power_sensor.close_resource()
    return {"isOpen": obs_test.power_sensor.get_open_status()}


@router_power_sensor.get("/getData")
async def get_data_power_sensor() -> dict[str, bool | str | float]:
    is_open = obs_test.power_sensor.get_open_status()

    if not is_open:
        return {"success": False, "errorMessage": "Not open: power sensor"}
    data = obs_test.power_sensor.get_data()
    if data is None:
        return {"success": False, "errorMessage": "Data none"}
    return {"success": True, "data": data}


@router_signal_analyzer.get("/connect")
async def connect_signal_analyzer() -> dict[str, bool]:
    return {"isOpen": obs_test.signal_analyzer.connect()}


@router_signal_analyzer.get("/disconnect")
async def disconnect_signal_analyzer() -> dict[str, bool]:
    obs_test.signal_analyzer.close_resource()
    return {"isOpen": obs_test.signal_analyzer.get_open_status()}


@router_signal_analyzer.get("/restart")
async def restart_signal_analyzer() -> dict[str, bool | str]:

    is_open = obs_test.signal_analyzer.get_open_status()
    if not is_open:
        return {"success": False, "errorMessage": "Not open: signal analyzer"}

    obs_test.signal_analyzer.send_restart_command()
    return {"success": True}


@router_signal_analyzer.get("/getTrace")
async def get_trace_signal_analyzer() -> dict[str, bool | str | FreqResponse]:

    is_open = obs_test.signal_analyzer.get_open_status()
    if not is_open:
        return {"success": False, "errorMessage": "Not open: signal analyzer"}
    data = obs_test.signal_analyzer.get_data(trace_num=1)
    if data is None:
        return {"success": False, "errorMessage": "Data none"}
    return {"success": True, "data": data}


@router_signal_analyzer.get("/getCapture")
async def get_capture_signal_analyzer(picture_name: str) -> dict[str, bool | str | list[int | float]]:

    is_open = obs_test.signal_analyzer.get_open_status()
    if not is_open:
        return {"success": False, "errorMessage": "Not open: signal analyzer"}
    data = obs_test.signal_analyzer.get_capture(picture_name="capture_test", deletes_picture=True)
    if data is None:
        return {"success": False, "errorMessage": "Data none"}

    if obs_test.p_save is None:
        return {"success": False, "errorMessage": "Not connect GDrive"}

    path = obs_test.p_save / f"{picture_name}.png"
    general.save_picture_from_binary_list(data=data, path=path)
    return {"success": True, "data": str(path)}


@router_test.get("/getChirpBeforeObs")
async def get_chirp_before_obs(test_name: str, duration: int) -> dict[str, bool | str]:

    is_open = obs_test.signal_analyzer.get_open_status()
    if not is_open:
        return {"success": False, "errorMessage": "Not open: signal analyzer"}
    if obs_test.get_busy_status():
        return {"success": False, "errorMessage": "busy"}
    if obs_test.p_save is None:
        return {"success": False, "errorMessage": "Not found: dir"}

    t = threading.Thread(
        target=obs_test.get_chirp_before_obs,
        args=[test_name, duration],
    )
    t.start()
    return {"success": True}


@router_test.get("/stopChirpBeforeObs")
async def stop_chirp_before_obs() -> dict[str, bool]:

    obs_test.set_not_busy()
    return {"success": True}


@router_test.get("/getObsData")
async def get_obs_data(test_name: str, wait_sec: int) -> dict[str, bool | str]:

    is_open = obs_test.signal_analyzer.get_open_status()
    if not is_open:
        return {"success": False, "errorMessage": "Not open: signal analyzer"}
    if obs_test.get_busy_status():
        return {"success": False, "errorMessage": "busy"}
    if obs_test.p_save is None:
        return {"success": False, "errorMessage": "Not found: dir"}

    t = threading.Thread(
        target=obs_test.get_obs_data,
        args=[test_name, wait_sec],
    )
    t.start()
    return {"success": True}
