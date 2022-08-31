from __future__ import annotations

import threading
from pathlib import Path
from time import perf_counter, sleep
from typing import Optional

from fastapi import APIRouter

import src.common.settings
from src.common import general
from src.common.decorator import exception
from src.common.general import get_today_string, resolve_path_shared_drives
from src.common.logger import set_logger
from src.engine.power_sensor import PowerSensor
from src.engine.read_instrument_settings import InstrumentSetting, read_json_file
from src.engine.signal_analyzer import FreqResponse, SignalAnalyzer

LOGGER_IS_ACTIVE_STREAM = src.common.settings.logger_is_active_stream
logger = set_logger(__name__, is_active_stream=LOGGER_IS_ACTIVE_STREAM)


class ObsTest:
    def __init__(self, settings: InstrumentSetting) -> None:
        self.__is_busy = False
        self.p_save = resolve_path_shared_drives(Path(settings.common.default_path))

        self.power_sensor = PowerSensor()
        self.power_sensor_data: Optional[dict[str, list[float]]] = None

        p_capture = Path(settings.signal_analyzer.capture_path)
        self.signal_analyzer = SignalAnalyzer(p_capture=p_capture)

    def set_busy(self) -> None:
        self.__is_busy = True

    def set_not_busy(self) -> None:
        self.__is_busy = False

    def get_busy_status(self) -> bool:
        return self.__is_busy

    def get_obs_data(self, test_name: str, obs_duration: int, warm_up_duration: int, hold_duration: int) -> Optional[dict[str, list[float]]]:
        def get_power_data() -> None:
            interval = 0.1
            elapsed_time = 0.0
            time_start = perf_counter()
            time_list: list[float] = []
            power_list: list[float] = []

            while elapsed_time <= (obs_duration + warm_up_duration):
                sleep(interval)
                elapsed_time = perf_counter() - time_start
                data = self.power_sensor.get_data()
                if data is not None:
                    time_list.append(elapsed_time)
                    power_list.append(data)
                if not self.get_busy_status():
                    break

            filename_stem = "obs"
            p_csv = p_dir / f"{filename_stem}.csv"
            dict_data = {"time": time_list, "power": power_list}
            self.power_sensor_data = dict_data
            general.save_csv_from_dict(data=dict_data, path=p_csv)

        self.set_busy()

        if self.p_save is not None:
            p_dir = self.p_save / test_name
            if not p_dir.exists():
                p_dir.mkdir()

            self.power_sensor_data = None
            t = threading.Thread(target=get_power_data)
            t.start()

            for test_num in range(warm_up_duration):
                if not self.get_busy_status():
                    break
                picture_name = f"before_obs_{test_num}"
                filename = f"{picture_name}.png"
                path = p_dir / filename
                data = self.signal_analyzer.get_capture(picture_name=picture_name, deletes_picture=True)
                if data is not None:
                    general.save_picture_from_binary_list(data=data, path=path)
                sleep(1)

            self.signal_analyzer.send_restart_command()
            filename_stem = "obs"
            p_png = p_dir / f"{filename_stem}.png"

            for _ in range(hold_duration):
                if not self.get_busy_status():
                    break
                sleep(1)

            if self.get_busy_status():
                capture = self.signal_analyzer.get_capture(picture_name=filename_stem, deletes_picture=True)
                if capture is not None:
                    general.save_picture_from_binary_list(data=capture, path=p_png)

            t.join()

        self.set_not_busy()

        return self.power_sensor_data


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
async def make_dir(pathStr: str, project: str) -> dict[str, bool | str]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        path = resolve_path_shared_drives(Path(pathStr))
        if path is None:
            return {"success": False, "error": "Not exist: dir"}
        p_dir = path / project / "auto_test" / "obs" / get_today_string()
        if not p_dir.exists():
            p_dir.mkdir(parents=True)
        obs_test.p_save = p_dir

        return {"success": True, "data": str(p_dir)}

    return wrapper()


@router_power_sensor.get("/connect")
async def connect_power_sensor(accessPoint: str) -> dict[str, bool]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool]:
        obs_test.power_sensor.connect(address=accessPoint)
        return {"success": True, "isOpen": obs_test.power_sensor.get_open_status()}

    return wrapper()


@router_power_sensor.get("/disconnect")
async def disconnect_power_sensor() -> dict[str, bool]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool]:
        obs_test.power_sensor.disconnect()
        return {"success": True, "isOpen": obs_test.power_sensor.get_open_status()}

    return wrapper()


@router_power_sensor.get("/getData")
async def get_data_power_sensor() -> dict[str, bool | str | float]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str | float]:
        is_open = obs_test.power_sensor.get_open_status()

        if not is_open:
            return {"success": False, "error": "Not open: power sensor"}
        data = obs_test.power_sensor.get_data()
        if data is None:
            return {"success": False, "error": "Data none"}
        return {"success": True, "data": data}

    return wrapper()


@router_signal_analyzer.get("/connect")
async def connect_signal_analyzer(accessPoint: str) -> dict[str, bool]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool]:
        obs_test.signal_analyzer.connect(address=accessPoint)
        return {"success": True, "isOpen": obs_test.signal_analyzer.get_open_status()}

    return wrapper()


@router_signal_analyzer.get("/disconnect")
async def disconnect_signal_analyzer() -> dict[str, bool]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool]:
        obs_test.signal_analyzer.disconnect()
        return {"success": True, "isOpen": obs_test.signal_analyzer.get_open_status()}

    return wrapper()


@router_signal_analyzer.get("/restart")
async def restart_signal_analyzer() -> dict[str, bool | str]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str]:
        is_open = obs_test.signal_analyzer.get_open_status()
        if not is_open:
            return {"success": False, "error": "Not open: signal analyzer"}

        obs_test.signal_analyzer.send_restart_command()
        return {"success": True}

    return wrapper()


@router_signal_analyzer.get("/getTrace")
async def get_trace_signal_analyzer() -> dict[str, bool | str | FreqResponse]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str | FreqResponse]:
        is_open = obs_test.signal_analyzer.get_open_status()
        if not is_open:
            return {"success": False, "error": "Not open: signal analyzer"}
        data = obs_test.signal_analyzer.get_data(trace_num=1)
        if data is None:
            return {"success": False, "error": "Data none"}
        return {"success": True, "data": data}

    return wrapper()


@router_signal_analyzer.get("/getCapture")
async def get_capture_signal_analyzer(pictureName: str) -> dict[str, bool | str | list[int | float]]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str | list[int | float]]:
        is_open = obs_test.signal_analyzer.get_open_status()
        if not is_open:
            return {"success": False, "error": "Not open: signal analyzer"}
        data = obs_test.signal_analyzer.get_capture(picture_name="capture_test", deletes_picture=True)
        if data is None:
            return {"success": False, "error": "Data none"}
        if obs_test.p_save is None:
            return {"success": False, "error": "Not connect GDrive"}
        if not obs_test.p_save.exists():
            return {"success": False, "error": "Not exist: dir"}

        path = obs_test.p_save / f"{pictureName}.png"
        general.save_picture_from_binary_list(data=data, path=path)
        return {"success": True, "data": str(path)}

    return wrapper()


@router_test.get("/startObs")
async def get_chirp_waveform(testName: str, obsDuration: int, warmUpDuration: int, holdDuration: int) -> dict[str, bool | str | dict[str, list[float]]]:  # noqa
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | str | dict[str, list[float]]]:
        is_open_power_sensor = obs_test.power_sensor.get_open_status()
        is_open_signal_analyzer = obs_test.signal_analyzer.get_open_status()
        if not is_open_power_sensor:
            return {"success": False, "error": "Not open: power sensor"}
        if not is_open_signal_analyzer:
            return {"success": False, "error": "Not open: signal analyzer"}
        if obs_test.get_busy_status():
            return {"success": False, "error": "busy"}
        if obs_test.p_save is None:
            return {"success": False, "error": "Not connect GDrive"}
        if not obs_test.p_save.exists():
            return {"success": False, "error": "Not exist: dir"}

        data = obs_test.get_obs_data(testName, obsDuration, warmUpDuration, holdDuration)
        if data is not None:
            return {"success": True, "data": data}
        else:
            return {"success": False, "error": "Data is none"}

    return wrapper()


@router_test.get("/stopObs")
async def stop_obs() -> dict[str, bool]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool]:
        obs_test.set_not_busy()
        return {"success": True}

    return wrapper()
