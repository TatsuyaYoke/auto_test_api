import json

import requests


def qmr_modcod_change_data(ip: str, port: str, modcod: int):

    print("qMR modcod change")
    endpoint = "rest/demodulatorWb1/_attribute/dvbs2ModCodExpected"
    headers = {"Content-Type": "application/json"}
    url = f"http://{ip}:{port}/{endpoint}"

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
    else:
        print("modcod setting error")
        return

    try:
        request_post = requests.post(url=url, data=json.dumps(payload), headers=headers, timeout=5)
        print(request_post.status_code)
    except requests.exceptions.ConnectTimeout:
        print("Timeout Error")
