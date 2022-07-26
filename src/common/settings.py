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
