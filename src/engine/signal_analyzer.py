from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, TypedDict

from src.common.general import get_now_string, get_today_string
from src.common.visa_driver import VisaDriver

SIGNAL_ANALYZER_IDN_PATTERN = "Keysight Technologies,N90([0-9]{2})(A|B),MY([0-9]+),A([0-9]*).([0-9]{2}).([0-9]{2})"

TraceNum = Literal[1, 2, 3, 4]


class FreqResponse(TypedDict):
    frequency: list[float]
    power: list[float]


class SignalAnalyzer(VisaDriver):
    def __init__(self, p_capture: Path) -> None:
        super().__init__()
        today_str = get_today_string()
        self.p_capture = p_capture / today_str

    def connect(self, address: str) -> bool:
        return self.set_resource(address=address, idn_pattern=SIGNAL_ANALYZER_IDN_PATTERN, read_termination="")

    def get_freq_start(self) -> Optional[float]:
        freq_start_str = self.query(data="freq:start?")
        if freq_start_str is None:
            return None
        else:
            return float(freq_start_str)

    def get_freq_stop(self) -> Optional[float]:
        freq_stop_str = self.query(data="freq:stop?")
        if freq_stop_str is None:
            return None
        else:
            return float(freq_stop_str)

    def get_data_points(self) -> Optional[int]:
        data_points_str = self.query(data="sweep:points?")
        if data_points_str is None:
            return None
        else:
            return int(data_points_str)

    def get_freq_list(self) -> Optional[list[float]]:
        """
        After getting start frequency, stop frequency, and number of points, make frequency list from them
        """
        freq_start = self.get_freq_start()
        if freq_start is None:
            return None

        freq_stop = self.get_freq_stop()
        if freq_stop is None:
            return None

        data_points = self.get_data_points()
        if data_points is None:
            return None

        if data_points != 1:
            freq_step = (freq_stop - freq_start) / (data_points - 1)
            return [freq_start + freq_step * x for x in range(data_points)]
        else:
            return None

    def send_restart_command(self) -> None:
        """
        Same as press "Restart" button
        """
        self.write("init")

    def trace_data(self, trace_num: TraceNum = 1) -> Optional[list[float]]:
        """
        Get power data as float array without frequency.
        """
        trace_data: Optional[str] = self.query(data=f"trace:data? trace{trace_num}")
        if trace_data is None:
            return None
        else:
            return list(map(float, trace_data.split(",")))

    def get_data(self, trace_num: TraceNum = 1) -> Optional[FreqResponse]:
        """
        Get power data as float array with frequency.
        """
        data_freq = self.get_freq_list()
        if data_freq is None:
            return None

        data_power = self.trace_data(trace_num)
        if data_power is None:
            return None

        if len(data_freq) != len(data_power):
            return None

        freq_response: FreqResponse = {"frequency": data_freq, "power": data_power}
        return freq_response

    def make_dir(self, path: Path) -> None:
        self.write(f'MMEM:MDIR "{path}"')

    def get_capture(self, picture_name: str = "capture", deletes_picture: bool = False) -> Optional[list[int | float]]:
        """
        - A picture is saved in the directory specified at init.
        - A filename is appended with the time of capture.
        - A picture in Signal Analyzer can be deleted when deletes_picture is True.
        - When saving a capture, you can use save_picture_from_binary_list in common/general.py.
        """

        now_str = get_now_string()
        picture_name_now = f"{picture_name}_{now_str}.png"

        self.write(data=f':MMEM:STOR:SCR "{self.p_capture / picture_name_now}"')
        capture = self.query_binary_values(f':MMEM:DATA? "{self.p_capture /picture_name_now}"')

        if deletes_picture:
            self.write(data=f':MMEM:DEL "{self.p_capture / picture_name_now}"')

        if capture is not None:
            return capture
        else:
            return None
