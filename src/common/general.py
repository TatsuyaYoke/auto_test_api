from __future__ import annotations

import struct
from datetime import datetime as dt
from pathlib import Path
from typing import Any

import pandas


def save_csv_from_dict(data: dict[Any, Any], path: Path) -> None:
    df = pandas.DataFrame(data=data)
    df.to_csv(path, index=False)


def save_picture_from_binary_list(data: list[int | float], path: Path) -> None:
    if len(data) != 0:
        with open(path, "wb") as fp:
            for byte in data:
                fp.write(struct.pack("B", byte))


def get_now_string() -> str:
    now = dt.now()
    now_str = now.strftime("%Y%m%d%H%M%S")
    return now_str


def get_today_string() -> str:
    today = dt.now()
    today_str = today.strftime("%Y%m%d")
    return today_str
