import time
from pathlib import Path

import pandas as pd
import pytest

import common.settings
from common import general
from engine.power_sensor import PowerSensor
from engine.read_instrument_settings import read_json_file

settings = read_json_file()
is_connected = common.settings.connect_power_sensor
if settings is not None and is_connected:
    address = settings.power_sensor.visa
    power_sensor = PowerSensor(address=address)

POWER_UPPER_LIMIT = 20
POWER_LOWER_LIMIT = -90


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_connect():
    assert power_sensor.connect()


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_power_sensor_single():
    data = power_sensor.get_data()
    assert data is not None
    assert POWER_LOWER_LIMIT < data < POWER_UPPER_LIMIT


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_power_sensor_loop():
    interval = 0.1
    measurement_duration = 3
    elapsed_time = 0
    time_start = time.perf_counter()
    time_list: list[float] = []
    power_list: list[float] = []

    while elapsed_time <= measurement_duration:
        time.sleep(interval)
        elapsed_time = time.perf_counter() - time_start
        data = power_sensor.get_data()
        if data is None:
            assert pytest.fail()
        else:
            time_list.append(elapsed_time)
            power_list.append(data)
            assert POWER_LOWER_LIMIT < data < POWER_UPPER_LIMIT

    p_dir = Path("csv")
    if not p_dir.exists():
        p_dir.mkdir()
    path = p_dir / "power_data.csv"

    dict_data = {"time": time_list, "power": power_list}
    general.save_csv_from_dict(data=dict_data, path=path)
    assert len(pd.read_csv(path).columns) == 2


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_close_inst():
    power_sensor.close_resource()
    assert not power_sensor.get_open_status()
