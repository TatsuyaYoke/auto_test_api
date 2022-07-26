import time

import pytest

from engine.gl840 import Gl840Visa
from engine.read_instrument_settings import read_json_file

is_release = True
GL840_VISA = Gl840Visa()
SETTING = read_json_file()
if SETTING is not None:
    GL840_SETTING = SETTING.gl840


def test_read_json_file():

    if GL840_SETTING is not None:
        print(GL840_SETTING)
        assert GL840_SETTING.visa.ip_address == "192.168.1.5"
        assert GL840_SETTING.visa.port == 8023

    assert GL840_SETTING is not None


@pytest.mark.skipif(is_release, reason="released")
def test_connect():

    if GL840_SETTING is not None:
        visa_setting = GL840_SETTING.visa
        assert GL840_VISA.connect(visa_setting)


@pytest.mark.skipif(is_release, reason="released")
def test_record():

    if GL840_VISA.get_open_status():
        assert GL840_VISA.record_start()
        time.sleep(3)
        assert not GL840_VISA.record_stop()


@pytest.mark.skipif(is_release, reason="released")
def test_get_all_data():

    if GL840_VISA.get_open_status():
        data = GL840_VISA.get_all_data()
        print(data)
        assert data is not None


@pytest.mark.skipif(is_release, reason="released")
def test_get_one_data():

    if GL840_VISA.get_open_status():
        data = GL840_VISA.get_one_data()
        print(data)
        assert data is not None


@pytest.mark.skipif(is_release, reason="released")
def test_channel_setting():

    if GL840_VISA.get_open_status():
        assert GL840_VISA.input_setting(channel="CH1", input_type="DC")
        assert GL840_VISA.range_setting(channel="CH1", range_type="20V")


@pytest.mark.skipif(is_release, reason="released")
def test_sampling_setting():

    if GL840_VISA.get_open_status():
        GL840_VISA.sampling_setting(sampling="5S")


@pytest.mark.skipif(is_release, reason="released")
def test_disconnect():

    if GL840_VISA.get_open_status():
        assert not GL840_VISA.close_resource()
