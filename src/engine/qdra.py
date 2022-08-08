from __future__ import annotations

import json
from pathlib import Path

import paramiko
import requests


def record_start(ip_address: str, port: int, session_name: str, session_desc: str, duration: int, timeout: int = 1) -> int:

    record_stop(ip_address, port)

    endpoint = "rest/dataRecorder5/_procedure/startRecording"
    url = f"http://{ip_address}:{port}/{endpoint}"
    payload = {
        "sessionName": {"factory": "Attribute", "factoryType": "string", "value": session_name},
        "sessionDesc": {"factory": "Attribute", "factoryType": "string", "value": session_desc},
        "startTime": {"factory": "Attribute", "factoryType": "time", "value": "1970-01-01 00:00:00"},
        "duration": {"factory": "Attribute", "factoryType": "int64", "value": duration},
    }
    try:
        request_post = requests.post(url=url, data=json.dumps(payload), timeout=timeout)
        return request_post.status_code
    except requests.exceptions.ConnectTimeout:
        return -1


def record_stop(ip_address: str, port: int, timeout: int = 1) -> int:

    endpoint = "rest/dataRecorder5/_procedure/stopRecording"
    url = f"http://{ip_address}:{port}/{endpoint}"

    try:
        request_post = requests.post(url=url, timeout=timeout)
        return request_post.status_code
    except requests.exceptions.ConnectTimeout:
        return -1


class QdraSsh:
    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def get_file(self, p_server: Path, p_save: Path) -> None:
        with paramiko.SSHClient() as ssh:
            # Are you sure you want to continue connecting (yes/no)? -> Yes
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password)
            sftp = ssh.open_sftp()
            sftp.get(str(p_server).replace("\\", "/"), str(p_save))

    def exec_sh(self, path: Path, sh_name: str, session_name: str) -> tuple[list[str], list[str]]:

        stdout_list: list[str] = []
        stderr_list: list[str] = []
        with paramiko.SSHClient() as ssh:
            # Are you sure you want to continue connecting (yes/no)? -> Yes
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password)
            path_str = str(path).replace("\\", "/")
            _, stdout, stderr = ssh.exec_command(f"cd {path_str} ; ./{sh_name} {session_name}")

            stdout_list.extend(stdout)
            stderr_list.extend(stderr)

        return stdout_list, stderr_list

    def get_list_dir(self, path: Path) -> list[str]:

        with paramiko.SSHClient() as ssh:
            # Are you sure you want to continue connecting (yes/no)? -> Yes
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password)
            sftp = ssh.open_sftp()
            list_dir = sftp.listdir(path=str(path).replace("\\", "/"))

        return list_dir
