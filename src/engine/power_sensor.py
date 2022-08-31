from typing import Optional

from src.common.visa_driver import VisaDriver

POWER_SENSOR_IDN_PATTERN = "Keysight Technologies,U([0-9]{4})X*(A|B),MY([0-9]+),A([0-9]*).([0-9]{2}).([0-9]{2})"


class PowerSensor(VisaDriver):
    def __init__(self) -> None:
        super().__init__()

    def connect(self, address: str) -> bool:
        return self.set_resource(address=address, idn_pattern=POWER_SENSOR_IDN_PATTERN, read_termination="")

    def get_data(self) -> Optional[float]:
        self.write(data="init")  # necessary before sending fetc?
        power_sensor_data = self.query(data="fetc?")
        if power_sensor_data is not None:
            return float(power_sensor_data)
        else:
            return None
