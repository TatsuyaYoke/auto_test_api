import json

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
