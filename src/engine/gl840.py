import re
from typing import Literal, Optional

from src.common.logger import set_logger
from src.common.visa_driver import VisaDriver
from src.engine.read_instrument_settings import VisaSetting

logger = set_logger(__name__)

IDN_PATTERN = r"\*IDN GRAPHTEC,GL840,([0-9]+),([0-9]+).([0-9]+)"
CHANNEL_PATTERN = r"CH([0-9]+)"

InputType = Literal["OFF", "DC", "TEMP"]
RangeType = Literal["20MV", "50MV", "100MV", "500MV", "1V", "2V", "5V", "10V", "20V", "50V", "100V"]
SamplingType = Literal[
    "10MS",
    "20MS",
    "50MS",
    "100MS",
    "125MS",
    "250MS",
    "500MS",
    "1S",
    "2S",
    "5S",
    "10S",
    "20S",
    "30S",
    "60S",
    "120S",
    "300S",
    "600S",
    "1200S",
    "1800S",
    "3600S",
]


class Gl840Visa(VisaDriver):
    def __init__(self) -> None:
        super().__init__()
        self.__is_recording = False

    def connect(self, visa_setting: VisaSetting) -> bool:

        visa_address = f"TCPIP0::{visa_setting.ip_address}::{visa_setting.port}::SOCKET"
        return super().set_resource(address=visa_address, idn_pattern=IDN_PATTERN)

    def record_start(self) -> bool:

        inst = super().get_inst()
        if inst is not None:
            inst.write(":MEAS:START")
            self.__is_recording = True

        return self.__is_recording

    def record_stop(self) -> bool:

        inst = super().get_inst()
        if inst is not None:
            inst.write(":MEAS:STOP")
            self.__is_recording = False

        return self.__is_recording

    def get_all_data(self) -> Optional[bytes]:
        """
        IDN response is added to the end of data
        """
        inst = super().get_inst()
        if inst is not None:
            inst.write(":MEAS:OUTP:ACK?")
            inst.write("*IDN?")  # request response data
            binary = inst.read_raw()
            return binary
        else:
            return None

    def get_one_data(self) -> Optional[bytes]:
        """
        IDN response is added to the end of data
        """
        inst = super().get_inst()
        if inst is not None:
            # clear buffers
            self.get_all_data()

            # get record one
            inst.write(":MEAS:OUTP:ONE?")
            inst.write("*IDN?")  # request response data
            binary = inst.read_raw()
            return binary
        else:
            return None

    def validate_channel(self, channel: str) -> bool:

        regex_pattern = re.compile(CHANNEL_PATTERN)
        if regex_pattern.fullmatch(channel.upper()) is not None:
            return True
        else:
            return False

    def input_setting(self, channel: str, input_type: InputType) -> bool:

        inst = super().get_inst()
        if inst is not None and self.validate_channel(channel):
            inst.write(f":AMP:{channel.upper()}:INP {input_type}")
            return True
        else:
            return False

    def range_setting(self, channel: str, range_type: RangeType) -> bool:
        inst = super().get_inst()
        if inst is not None and self.validate_channel(channel):
            inst.write(f":AMP:{channel.upper()}:RANG {range_type}")
            return True
        else:
            return False

    def sampling_setting(self, sampling: SamplingType) -> None:

        inst = super().get_inst()
        if inst is not None:
            inst.write(f":DATA:SAMP {sampling}")
