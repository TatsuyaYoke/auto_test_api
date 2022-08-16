from __future__ import annotations

import struct
from datetime import datetime as dt
from pathlib import Path
from typing import Any, Optional

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


def resolve_path_jp_en(path: str | Path, resolve_path_name1: str, resolve_path_name2: str) -> Optional[Path]:

    path_str = str(path)

    if resolve_path_name1 in path_str:
        if Path(path_str).exists():
            return Path(path_str)
        else:
            path_str = path_str.replace(resolve_path_name1, resolve_path_name2)
            if Path(path_str).exists():
                return Path(path_str)
            else:
                return None
    elif resolve_path_name2 in path_str:
        if Path(path_str).exists():
            return Path(path_str)
        else:
            path_str = path_str.replace(resolve_path_name2, resolve_path_name1)
            if Path(path_str).exists():
                return Path(path_str)
            else:
                return None
    else:
        return None


def resolve_path_shared_drives(path: str | Path) -> Optional[Path]:

    return resolve_path_jp_en(path, "共有ドライブ", "Shared drives")
