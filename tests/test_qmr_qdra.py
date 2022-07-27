from engine.qdra import record_start, record_stop
from engine.qmr import change_modcod
from engine.read_instrument_settings import read_json_file

SETTING = read_json_file()
if SETTING is not None:
    QMR_SETTING = SETTING.qmr
    QDRA_SETTING = SETTING.qdra


def test_read_json_file():

    if QMR_SETTING is not None:
        print(QMR_SETTING)
        assert QMR_SETTING.network.ip_address == "192.168.12.4"
        assert QMR_SETTING.network.port == 80

    assert QMR_SETTING is not None

    if QDRA_SETTING is not None:
        print(QDRA_SETTING)
        assert QDRA_SETTING.network.ip_address == "192.168.12.5"
        assert QDRA_SETTING.network.port == 8081

    assert QDRA_SETTING is not None


def test_qmr():

    ip_address = QMR_SETTING.network.ip_address
    port = QMR_SETTING.network.port
    assert change_modcod(ip_address=ip_address, port=port, modcod=13) == -1


def test_qdra():

    ip_address = QDRA_SETTING.network.ip_address
    port = QDRA_SETTING.network.port
    session_name = "dummy"
    session_desc = ""
    duration = 10
    assert record_start(ip_address=ip_address, port=port, session_name=session_name, session_desc=session_desc, duration=duration) == -1
    assert record_stop(ip_address=ip_address, port=port) == -1
