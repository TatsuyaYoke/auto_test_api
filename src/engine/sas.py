from __future__ import annotations

import threading
import time
from typing import Literal, Optional, TypedDict

from src.common.logger import set_logger
from src.common.serial_driver import SerialDriver
from src.engine.read_instrument_settings import SasOutputSetting, SasRepeatSetting

logger = set_logger(__name__)


class SasOutputSettingDict(TypedDict):
    voc: float
    isc: float
    fill_factor: float


class SasDataDict(TypedDict):
    time: int
    voltage: Optional[float]
    current: Optional[float]


class SasResponseDict(TypedDict):
    is_open: bool
    is_connection_error: bool
    output_setting: SasOutputSettingDict
    data: SasDataDict
    is_on: bool
    repeat_on: bool
    is_range_error: bool


SAS_DEFAULT_OUTPUT_SETTING: SasOutputSettingDict = {"voc": 50, "isc": 0.1, "fill_factor": 0.9}

SAS_CMD_VOC_MAX = 100
SAS_CMD_VOC_MIN = 50
SAS_CMD_ISC_MAX = 4
SAS_CMD_ISC_MIN = 0.1

SAS_DATA_HEADER = "10120020"
SAS_DATA_LENGTH = 32
# There is no plan to use 2 channels. If use several channels, it is possible extend
SAS_DATA_POSITION = {"CH1": {"voltage": {"start": 6, "end": 7}, "current": {"start": 8, "end": 9}}}


def binary_hex_str_to_array(cmd: str, sep: Optional[str] = None) -> list[int]:  # TODO general function
    """
    Convert from hex string command to integer array
    Ex) "FF 01 00 02" or "FF010002" => [255, 1, 0, 2]

    Parameters
    ----------
    cmd : str
        Hex string command
        Ex) "FF 01 00 02"

    sep : str, optional
        separation string, by default " "
        If separation of a command has "," like "FF,01,00,02", you have to set ",".

    Returns
    -------
    list[int]
    """
    num_split = 2
    if sep is None:
        cmd_arr = [cmd[i : i + num_split] for i in range(0, len(cmd), num_split)]
    else:
        cmd_arr = list(filter(lambda x: x != "", cmd.split(sep)))

    return list(map(lambda x: int(x, base=16), cmd_arr))


class SasSerial(SerialDriver):
    def __init__(self) -> None:
        super().__init__()
        self.__is_on = False
        self.__repeat_on = False
        self.__is_range_error = False
        self.__output_setting = SAS_DEFAULT_OUTPUT_SETTING
        self.__data: SasDataDict = {"time": int(time.time()), "voltage": None, "current": None}

    def get_output_status(self) -> bool:
        return self.__is_on

    def get_output_setting(self) -> SasOutputSettingDict:
        return self.__output_setting

    def get_data(self) -> SasDataDict:
        return self.__data

    def get_range_error_status(self) -> bool:
        return self.__is_range_error

    def set_data_none(self) -> None:
        self.__data = {"time": int(time.time()), "voltage": None, "current": None}

    def make_check_sum(self, tmtc_wo_checksum: str, sep: Optional[str] = None) -> str:

        num_split = 2
        if sep is None:
            tmtc_arr = [tmtc_wo_checksum[i : i + num_split] for i in range(0, len(tmtc_wo_checksum), num_split)]
        else:
            tmtc_arr = list(filter(lambda x: x != "", tmtc_wo_checksum.split(sep)))
        tmtc_sum = 0

        for byte in tmtc_arr:
            tmtc_sum += int(byte, 16)

        tmp = format(tmtc_sum, "04X")

        if sep is None:
            return tmp[:2] + tmp[2:4]
        else:
            return tmp[:2] + sep + tmp[2:4]

    def output(self, onoff: Literal["on", "off"] = "off", setting: Optional[SasOutputSetting] = None) -> None:

        """
        Control SAS output on/off status.
        When SAS outputs on, output setting can be set.
        When SAS outputs off, output setting will be set default value.

        Parameters
        ----------
        onoff: "on" | "off"
        output_setting: SasOutputSetting (class), optional
            class SasOutputSetting(BaseModel):
                voc: float
                isc: float
                fill_factor: float
            It is not necessary to set when SAS outputs off because default value will be set.

        """

        def validate_output_range(output_setting: SasOutputSettingDict) -> bool:

            is_error = False

            voc = float(output_setting["voc"])
            isc = float(output_setting["isc"])
            fill_factor = float(output_setting["fill_factor"])

            if not (SAS_CMD_VOC_MIN <= voc <= SAS_CMD_VOC_MAX):
                is_error = True
            if not (SAS_CMD_ISC_MIN <= isc <= SAS_CMD_ISC_MAX):
                is_error = True
            if not (0 <= fill_factor <= 1):
                is_error = True

            if is_error:
                logger.error("SAS output setting range error!")

            return not is_error

        output_setting: SasOutputSettingDict
        if setting is None or onoff == "off":
            output_setting = SAS_DEFAULT_OUTPUT_SETTING
        else:
            output_setting = {
                "voc": setting.voc,
                "isc": setting.isc,
                "fill_factor": setting.fill_factor,
            }

        if validate_output_range(output_setting):
            self.__is_range_error = False
            self.__output_setting = output_setting
            self.__is_on = False if onoff == "off" else True

            cmd = "10 02 00 18 "  # header
            cmd += "00 " if onoff == "off" else "01 "  # off:00, on:01
            cmd += "00 01 "  # Array No.1
            cmd += "00 "  # IV No.0

            voc_float = float(output_setting["voc"])
            isc_float = float(output_setting["isc"])
            fill_factor_float = float(output_setting["fill_factor"])

            pmax = voc_float * isc_float * fill_factor_float

            cmd_pmax_set = format(int(pmax), "04X")
            cmd_voc_set = format(int(voc_float * 10), "04X")
            cmd_ff_set = format(int(fill_factor_float * 10000), "04X")
            cmd_para_set_arr = [
                cmd_pmax_set[:2],
                cmd_pmax_set[2:4],
                cmd_voc_set[:2],
                cmd_voc_set[2:4],
                cmd_ff_set[:2],
                cmd_ff_set[2:4],
            ]
            cmd_para_set = " ".join(cmd_para_set_arr)
            cmd += cmd_para_set + " "
            cmd += "FF FF FF FF FF FF FF FF "  # dummy 8byte
            cmd += self.make_check_sum(cmd, sep=" ")
            self.send_binary_array(binary_hex_str_to_array(cmd, sep=" "))

        else:
            self.__is_range_error = True

    def receive_data(self) -> SasResponseDict:

        voltage = None
        current = None
        binary = self.receive_binary()

        # Validations are below.
        # 1. Header
        # 2. Length
        # 3. Check sum
        if binary is not None:
            header_position = binary.rfind(SAS_DATA_HEADER)

            if header_position > -1:
                binary_chunk = binary[header_position : header_position + SAS_DATA_LENGTH * 2]
                if len(binary_chunk) == SAS_DATA_LENGTH * 2:
                    binary_chunk_wo_check_sum = binary_chunk[:-4]
                    check_sum = binary_chunk[-4:]
                    if self.make_check_sum(binary_chunk_wo_check_sum) == check_sum.upper():
                        voltage = (
                            int(
                                binary_chunk[SAS_DATA_POSITION["CH1"]["voltage"]["start"] * 2 : (SAS_DATA_POSITION["CH1"]["voltage"]["end"] + 1) * 2],
                                16,
                            )
                            / 10
                        )
                        current = (
                            int(
                                binary_chunk[SAS_DATA_POSITION["CH1"]["current"]["start"] * 2 : (SAS_DATA_POSITION["CH1"]["current"]["end"] + 1) * 2],
                                16,
                            )
                            / 10
                        )

        data: SasDataDict = {"time": int(time.time()), "voltage": voltage, "current": current}
        self.__data = data

        return self.response()

    def response(self) -> SasResponseDict:

        response: SasResponseDict = {
            # General response
            "is_open": super().get_port_status(),
            "is_connection_error": super().get_connection_status(),
            "output_setting": self.__output_setting,
            "data": self.__data,
            # Special response
            "is_on": self.__is_on,
            "repeat_on": self.__repeat_on,
            "is_range_error": self.__is_range_error,
        }

        return response

    def get_repeat_status(self) -> bool:
        return self.__repeat_on

    def repeat_on(
        self,
        output_setting: SasOutputSetting,
        repeat_setting: SasRepeatSetting,
    ) -> None:

        """
        Repeat SAS on/off at regular interval.

        Parameters
        ----------
        output_setting: SasOutputSetting (class)
            class SasOutputSetting(BaseModel):
                voc: float
                isc: float
                fill_factor: float

        repeat_setting: SasORpeatSetting (class)
            class SasRepeatSetting(BaseModel):
                orbit_period: int
                sun_rate: float
                offset: int
                sleep_time: int

        """

        def output_setting_thread(elapsed_time: int) -> None:
            if (elapsed_time + offset) % orbit_period < sun_duration:
                self.output(onoff="on", setting=output_setting)
            else:
                self.output(onoff="off")

        def repeat_thread() -> None:
            elapsed_time = 0
            base_time = time.time()
            while self.get_repeat_status():
                output_setting_thread(elapsed_time=elapsed_time)
                t = threading.Thread(target=output_setting_thread, args=(elapsed_time,))
                t.start()
                next_time = (base_time - time.time()) % interval
                time.sleep(next_time)
                elapsed_time += interval

        orbit_period = repeat_setting.orbit_period
        sun_duration = int(orbit_period * repeat_setting.sun_rate)
        offset = repeat_setting.offset
        interval = repeat_setting.interval
        self.__repeat_on = True

        t = threading.Thread(target=repeat_thread)
        t.start()

    def repeat_off(self) -> None:
        self.__repeat_on = False
        self.output("off")
