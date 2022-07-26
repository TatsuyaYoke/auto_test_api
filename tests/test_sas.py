from engine.read_instrument_settings import read_json_file

is_release = True
SETTING = read_json_file()
if SETTING is not None:
    SAS_SETTING = SETTING.sas


def test_read_json_file():

    if SAS_SETTING is not None:
        print(SAS_SETTING)
        assert SAS_SETTING.serial.port == "COM1"
        assert SAS_SETTING.serial.baudrate == 57600
        assert SAS_SETTING.serial.parity == "E"
        assert SAS_SETTING.output.voc == 80
        assert SAS_SETTING.output.isc == 4
        assert SAS_SETTING.output.fill_factor == 0.9
        assert SAS_SETTING.repeat.orbit_period == 10
        assert SAS_SETTING.repeat.sun_rate == 0.6
        assert SAS_SETTING.repeat.offset == 0

    assert SAS_SETTING is not None
