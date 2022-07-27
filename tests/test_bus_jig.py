from engine.bus_jig import BusJigSerial
from engine.read_instrument_settings import read_json_file

is_release = True
BUS_JIG_SERIAL = BusJigSerial()
SETTING = read_json_file()
if SETTING is not None:
    BUS_SETTING = SETTING.bus


def test_read_json_file():

    if BUS_SETTING is not None:
        print(BUS_SETTING)
        assert BUS_SETTING.serial.port == "COM1"
        assert BUS_SETTING.serial.baudrate == 9600
        assert BUS_SETTING.serial.parity == "N"

    assert BUS_SETTING is not None


def test_sat_ena_dis():

    port = BUS_SETTING.serial.port
    baudrate = BUS_SETTING.serial.baudrate
    parity = BUS_SETTING.serial.parity
    BUS_JIG_SERIAL.set_port(port=port, baudrate=baudrate, parity=parity)
    assert BUS_JIG_SERIAL.get_port_status()
    BUS_JIG_SERIAL.send_sat_ena()
    BUS_JIG_SERIAL.send_sat_dis()


def test_close_port():

    BUS_JIG_SERIAL.close_port()
    assert not BUS_JIG_SERIAL.get_port_status()
