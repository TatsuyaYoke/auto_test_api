from __future__ import annotations

from src.common.serial_driver import SerialDriver


class BusJigSerial(SerialDriver):
    def __init__(self) -> None:
        super().__init__()
        self.__is_ena = False

    def get_status(self) -> bool:
        return self.__is_ena

    def send_sat_ena(self) -> None:
        super().send_ascii("ENA")

    def send_sat_dis(self) -> None:
        super().send_ascii("DIS")
