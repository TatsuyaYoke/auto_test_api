from __future__ import annotations

import re
from typing import Optional

from pyvisa.highlevel import ResourceManager
from pyvisa.resources.tcpip import TCPIPSocket


class VisaDriver:
    def __init__(self) -> None:
        self.__rm: Optional[ResourceManager] = None
        self.__inst: Optional[TCPIPSocket] = None
        self.__is_open = False

    def set_resource(self, address: str, idn_pattern: str, read_termination: str = "\r\n", write_termination: str = "\r\n") -> bool:  # FIXME
        self.__rm = ResourceManager()
        self.__inst = TCPIPSocket(resource_manager=self.__rm, resource_name=address)
        self.__inst.open()
        self.__inst.read_termination = read_termination
        self.__inst.write_termination = write_termination
        self.__inst.timeout = 10000  # ms

        idn_response = self.__inst.query("*IDN?")
        regex_pattern = re.compile(idn_pattern)

        if idn_response is not None:
            if regex_pattern.fullmatch(idn_response) is not None:
                self.__is_open = True
            else:
                self.__is_open = False
        else:
            self.__is_open = False

        return self.__is_open

    def close_resource(self) -> bool:
        self.__is_open = False
        if self.__rm is not None and self.__inst is not None:
            self.__inst.close()
            self.__rm.close()

        return self.__is_open

    def get_inst(self) -> Optional[TCPIPSocket]:
        return self.__inst

    def get_open_status(self) -> bool:
        return self.__is_open
