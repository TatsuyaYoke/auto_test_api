import os
from pathlib import Path
from time import sleep

import pandas
import pytest

import common.settings
from common import general
from engine.read_instrument_settings import read_json_file
from engine.signal_analyzer import SignalAnalyzer

NUM_TEST_LOOP = 5

settings = read_json_file()
is_connected = common.settings.connect_signal_analyzer
if settings is not None and is_connected:
    address = settings.signal_analyzer.visa
    p_capture = Path(settings.signal_analyzer.capture_path)
    signal_analyzer = SignalAnalyzer(address=address, p_capture=p_capture)


def test_check_setting():
    assert address == "TCPIP0::192.168.3.240::inst0::INSTR"
    assert p_capture == Path("D:/Users/Instrument/Documents/SA/screen")


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_connect():
    assert signal_analyzer.connect()


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_get_freq_start():
    freq_start = signal_analyzer.get_freq_start()
    assert freq_start is not None
    assert freq_start == 2227750000


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_get_freq_stop():
    freq_stop = signal_analyzer.get_freq_stop()
    assert freq_stop is not None
    assert freq_stop == 2228250000


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_get_data_points():
    data_points = signal_analyzer.get_data_points()
    assert data_points is not None
    assert data_points == 1001


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_get_freq_list():
    signal_analyzer.send_restart_command()
    freq_list = signal_analyzer.get_freq_list()
    assert freq_list is not None
    assert len(freq_list) == 1001

    # Verification of whether the frequency interval is constant
    is_ok = True
    step = freq_list[1] - freq_list[0]
    for data_num in range(2, 1001):
        if freq_list[data_num] - freq_list[data_num - 1] != step:
            print(step, freq_list[data_num] - freq_list[data_num - 1])
            is_ok = False
    assert is_ok


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_trace_data_single():
    signal_analyzer.send_restart_command()
    power_data = signal_analyzer.trace_data(trace_num=1)
    assert power_data is not None
    assert len(power_data) == 1001


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_freq_response_single():
    signal_analyzer.send_restart_command()
    freq_response = signal_analyzer.get_data(trace_num=1)
    assert freq_response is not None
    assert list(freq_response.keys())[0] == "frequency"
    assert list(freq_response.keys())[1] == "power"
    assert len(freq_response["frequency"]) == 1001
    assert len(freq_response["power"]) == 1001


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_get_capture_single():
    p_dir = Path("capture")
    if not p_dir.exists():
        p_dir.mkdir()
    picture_name = "test_capture"
    path = p_dir / f"{picture_name}.png"

    signal_analyzer.send_restart_command()
    capture = signal_analyzer.get_capture(picture_name=picture_name, deletes_picture=True)
    assert capture is not None
    general.save_picture_from_binary_list(data=capture, path=path)
    assert os.path.isfile(path)


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_save_freq_response_to_csv():
    p_dir = Path("csv")
    if not p_dir.exists():
        p_dir.mkdir()
    path = p_dir / "test_data.csv"
    signal_analyzer.send_restart_command()
    freq_response = signal_analyzer.get_data(trace_num=1)
    assert freq_response is not None
    freq_response_dict = dict(freq_response)  # pandas.DataFrame does not accept TypedDict types.
    general.save_csv_from_dict(data=freq_response_dict, path=path)
    columns_length = len(pandas.read_csv(path).columns)
    assert columns_length == 2


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_trace_data_loop():
    for _ in range(NUM_TEST_LOOP):
        signal_analyzer.send_restart_command()
        power_data = signal_analyzer.trace_data(trace_num=1)
        assert power_data is not None
        assert len(power_data) == 1001


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_freq_response_loop():
    for _ in range(NUM_TEST_LOOP):
        signal_analyzer.send_restart_command()
        freq_response = signal_analyzer.get_data(trace_num=1)
        assert freq_response is not None
        assert list(freq_response.keys())[0] == "frequency"
        assert list(freq_response.keys())[1] == "power"
        assert len(freq_response["frequency"]) == 1001
        assert len(freq_response["power"]) == 1001


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_get_capture_loop():
    p_dir = Path("capture")
    if not p_dir.exists():
        p_dir.mkdir()

    for test_num in range(NUM_TEST_LOOP):
        picture_name = f"test_capture_{test_num}"
        path = p_dir / f"{picture_name}.png"
        signal_analyzer.send_restart_command()
        capture = signal_analyzer.get_capture(picture_name=picture_name, deletes_picture=False)
        assert capture is not None
        general.save_picture_from_binary_list(data=capture, path=path)
        assert os.path.isfile(path)
        sleep(1)


@pytest.mark.skipif(not is_connected, reason="not connected")
def test_close_inst():
    signal_analyzer.close_resource()
    assert not signal_analyzer.get_open_status()
