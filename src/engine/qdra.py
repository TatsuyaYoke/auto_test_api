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
        request = request_post.json()
        if request["startRecordingResponse"]["value"]:
            return request_post.status_code
        else:
            return -1
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

    def exec_sh(self, session_name: str, path: Path, p_script: Path) -> tuple[str, str]:

        stdout_list: list[str] = []
        stderr_list: list[str] = []
        with paramiko.SSHClient() as ssh:
            # Are you sure you want to continue connecting (yes/no)? -> Yes
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password)
            path_str = str(path).replace("\\", "/")
            p_script_str = str(p_script).replace("\\", "/")
            stdin, stdout, stderr = ssh.exec_command(f"cd ~/{path_str} ; ~/{p_script_str} {session_name}", get_pty=True)
            stdin.write(f"{self.password}\n")
            stdin.flush()

            stdout_list.extend(stdout)
            stderr_list.extend(stderr)

        return "".join(stdout_list), "".join(stderr_list)

    def delete_dir(self, path: Path) -> tuple[list[str], list[str]]:

        stdout_list: list[str] = []
        stderr_list: list[str] = []
        with paramiko.SSHClient() as ssh:
            # Are you sure you want to continue connecting (yes/no)? -> Yes
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password)
            path_str = str(path).replace("\\", "/")
            stdin, stdout, stderr = ssh.exec_command(f"rm -r ~/{path_str}", get_pty=True)
            stdin.write(f"{self.password}\n")
            stdin.flush()

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

    def exists(self, path: Path) -> bool:

        with paramiko.SSHClient() as ssh:
            # Are you sure you want to continue connecting (yes/no)? -> Yes
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password)
            sftp = ssh.open_sftp()
            try:
                sftp.stat(str(path).replace("\\", "/"))
                return True
            except FileNotFoundError:
                return False

    def mkdir(self, path: Path) -> bool:

        with paramiko.SSHClient() as ssh:
            # Are you sure you want to continue connecting (yes/no)? -> Yes
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.host, self.port, self.username, self.password)
            sftp = ssh.open_sftp()

            path_tmp = path
            path_list: list[Path] = []
            path_list.append(path)
            path_depth = len(str(path).split("\\"))
            for _ in range(path_depth - 1):
                path_tmp = path_tmp.parent
                path_list.append(path_tmp)

            path_list.reverse()

            for p in path_list:
                try:
                    sftp.stat(str(p).replace("\\", "/"))
                except FileNotFoundError:
                    sftp.mkdir(str(p).replace("\\", "/"))

        return self.exists(path)
