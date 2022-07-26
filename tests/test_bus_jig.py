from engine.read_instrument_settings import read_json_file

is_release = True
SETTING = read_json_file()
if SETTING is not None:
    BUS_SETTING = SETTING.bus


def test_read_json_file():

    if BUS_SETTING is not None:
        print(BUS_SETTING)
        assert BUS_SETTING.serial.port == "COM5"
        assert BUS_SETTING.serial.baudrate == 9600
        assert BUS_SETTING.serial.parity == "N"

    assert BUS_SETTING is not None
