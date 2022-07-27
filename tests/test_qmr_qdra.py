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
