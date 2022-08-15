import os
import sys
from pathlib import Path

from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    p_this_file = Path(sys.executable)
    p_parent = p_this_file.resolve().parent
else:
    p_this_file = Path(__file__)
    p_parent = p_this_file.resolve().parent.parent.parent

P_DOT_ENV_FILE = p_parent / ".env"

load_dotenv(P_DOT_ENV_FILE)

logger_is_active_stream = False
LOGGER_IS_ACTIVE_STREAM = os.getenv("LOGGER_IS_ACTIVE_STREAM")
if LOGGER_IS_ACTIVE_STREAM is not None and LOGGER_IS_ACTIVE_STREAM.lower() == "true":
    logger_is_active_stream = True

connect_power_sensor = True
CONNECT_POWER_SENSOR = os.getenv("CONNECT_POWER_SENSOR")
if CONNECT_POWER_SENSOR is not None and CONNECT_POWER_SENSOR.lower() == "false":
    connect_power_sensor = False

connect_signal_analyzer = True
CONNECT_SIGNAL_ANALYZER = os.getenv("CONNECT_SIGNAL_ANALYZER")
if CONNECT_SIGNAL_ANALYZER is not None and CONNECT_SIGNAL_ANALYZER.lower() == "false":
    connect_signal_analyzer = False
