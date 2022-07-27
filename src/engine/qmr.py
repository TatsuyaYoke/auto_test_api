import json
from typing import Literal

import requests

ModcodType = Literal[13, 15]


def change_modcod(ip_address: str, port: int, modcod: ModcodType, timeout: int = 1) -> int:

    endpoint = "rest/demodulatorWb1/_attribute/dvbs2ModCodExpected"
    headers = {"Content-Type": "application/json"}
    url = f"http://{ip_address}:{port}/{endpoint}"

    payload = {
        "dvbs2ModCodExpected": {
            "factory": "Attribute",
            "factoryType": "string",
        }
    }

    if modcod == 13:
        payload["dvbs2ModCodExpected"]["value"] = "8PSK 2/3"
    elif modcod == 15:
        payload["dvbs2ModCodExpected"]["value"] = "8PSK 5/6"

    try:
        request_post = requests.post(url=url, data=json.dumps(payload), headers=headers, timeout=timeout)
        return request_post.status_code
    except requests.exceptions.ConnectTimeout:
        return -1
