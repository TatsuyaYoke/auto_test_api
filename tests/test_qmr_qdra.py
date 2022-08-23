from pathlib import Path
from uuid import uuid4

import pytest

from engine.qdra import QdraSsh, record_start, record_stop
from engine.qmr import change_modcod
from engine.read_instrument_settings import read_json_file

SETTING = read_json_file()
if SETTING is not None:
    QMR_SETTING = SETTING.qmr
    QDRA_SETTING = SETTING.qdra
    TRANS_SETTING = SETTING.trans


def test_read_json_file():

    print(QMR_SETTING)
    assert QMR_SETTING.network.ip_address == "192.168.12.4"
    assert QMR_SETTING.network.port == 80

    print(QDRA_SETTING)
    assert QDRA_SETTING.network.ip_address == "192.168.12.5"
    assert QDRA_SETTING.network.port == 8081
    assert QDRA_SETTING.ssh.ip_address == "192.168.12.5"
    assert QDRA_SETTING.ssh.port == 22
    assert QDRA_SETTING.ssh.username == "synspective"
    assert QDRA_SETTING.ssh.password == "strix"

    print(TRANS_SETTING)
    assert TRANS_SETTING.ignore_file_extension == ["bin"]
    assert TRANS_SETTING.ignore_file == []


def test_qmr():

    ip_address = QMR_SETTING.network.ip_address
    port = QMR_SETTING.network.port
    assert change_modcod(ip_address=ip_address, port=port, modcod=15) == 200


@pytest.mark.skip()
def test_qdra():

    ip_address = QDRA_SETTING.network.ip_address
    port = QDRA_SETTING.network.port
    session_name = str(uuid4())
    session_desc = ""
    duration = 10
    assert record_start(ip_address=ip_address, port=port, session_name=session_name, session_desc=session_desc, duration=duration) == 200
    assert record_stop(ip_address=ip_address, port=port) == 200


def test_qdra_get_file():

    ip_address = QDRA_SETTING.ssh.ip_address
    port = QDRA_SETTING.ssh.port
    username = QDRA_SETTING.ssh.username
    password = QDRA_SETTING.ssh.password

    qdra_ssh = QdraSsh(host=ip_address, port=port, username=username, password=password)

    p_server = Path("12TB/dsx0201_final/0801_24hs_6_Ocean2/waveform_and_spectrum_cal.png")
    p_save = Path("out.png")

    qdra_ssh.get_file(p_server=p_server, p_save=p_save)
    assert p_save.exists()
    p_save.unlink(missing_ok=True)


def test_qdra_exec_sh():

    ip_address = QDRA_SETTING.ssh.ip_address
    port = QDRA_SETTING.ssh.port
    username = QDRA_SETTING.ssh.username
    password = QDRA_SETTING.ssh.password

    qdra_ssh = QdraSsh(host=ip_address, port=port, username=username, password=password)

    path = Path("12TB/temporary/work")
    p_script = Path("12TB/temporary/script/data_processing_v4.sh")  # TODO
    session_name = "E2E_SET2_1_unset"
    stdout, stderr = qdra_ssh.exec_sh(session_name=session_name, path=path, p_script=p_script)
    for out in stdout:
        print(out, end="")
    for out in stderr:
        print(out, end="")
    list_dir = qdra_ssh.get_list_dir(path / session_name)
    assert len(list_dir) > 0


@pytest.mark.skip()
def test_qdra_exists():

    ip_address = QDRA_SETTING.ssh.ip_address
    port = QDRA_SETTING.ssh.port
    username = QDRA_SETTING.ssh.username
    password = QDRA_SETTING.ssh.password

    qdra_ssh = QdraSsh(host=ip_address, port=port, username=username, password=password)
    assert qdra_ssh.exists(Path("12TB"))
    assert not qdra_ssh.exists(Path("11TB"))
    assert qdra_ssh.exists(Path("12TB/dsx0201_final"))
    assert not qdra_ssh.exists(Path("12TB/sx0201_final"))
    assert qdra_ssh.exists(Path("12TB/dsx0201_final/data_processing_v4.sh"))
    assert not qdra_ssh.exists(Path("12TB/dsx0201_final/data.sh"))


@pytest.mark.skip()
def test_qdra_mkdir():

    ip_address = QDRA_SETTING.ssh.ip_address
    port = QDRA_SETTING.ssh.port
    username = QDRA_SETTING.ssh.username
    password = QDRA_SETTING.ssh.password

    qdra_ssh = QdraSsh(host=ip_address, port=port, username=username, password=password)
    assert qdra_ssh.mkdir(Path("12TB/dsx0201_final/testDummy"))
    assert qdra_ssh.mkdir(Path("12TB/projectDummy/testDummy"))


@pytest.mark.skip()
def test_qdra_delete_dir():

    ip_address = QDRA_SETTING.ssh.ip_address
    port = QDRA_SETTING.ssh.port
    username = QDRA_SETTING.ssh.username
    password = QDRA_SETTING.ssh.password

    qdra_ssh = QdraSsh(host=ip_address, port=port, username=username, password=password)
    path = Path("12TB/temporary/work/E2E_SET2_1_unset")
    qdra_ssh.delete_dir(path=path)
