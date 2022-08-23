from __future__ import annotations

import psutil
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import src.common.settings
import src.routers.bus
import src.routers.obs
import src.routers.trans
from src.common.decorator import exception
from src.common.logger import set_logger

API_NAME = "sat_auto_test_api"
LOGGER_IS_ACTIVE_STREAM = src.common.settings.logger_is_active_stream
logger = set_logger(__name__, is_active_stream=LOGGER_IS_ACTIVE_STREAM)

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(src.routers.bus.router, prefix="/bus", tags=["bus"])
app.include_router(src.routers.obs.router, prefix="/obs", tags=["obs"])
app.include_router(src.routers.obs.router_common, prefix="/obs/common", tags=["obs"])
app.include_router(src.routers.obs.router_power_sensor, prefix="/obs/power_sensor", tags=["obs"])
app.include_router(src.routers.obs.router_signal_analyzer, prefix="/obs/signal_analyzer", tags=["obs"])
app.include_router(src.routers.obs.router_test, prefix="/obs/test", tags=["obs"])
app.include_router(src.routers.trans.router, prefix="/trans", tags=["trans"])
app.include_router(src.routers.trans.router_common, prefix="/trans/common", tags=["trans"])
app.include_router(src.routers.trans.router_qdra, prefix="/trans/qdra", tags=["trans"])
app.include_router(src.routers.trans.router_qmr, prefix="/trans/qmr", tags=["trans"])
app.include_router(src.routers.trans.router_test, prefix="/trans/test", tags=["trans"])


@app.get("/")
async def read_root() -> dict[str, bool]:
    return {"success": True}


@app.get("/getPid")
async def get_pid() -> dict[str, bool | list[int]]:
    @exception(logger=logger)
    def wrapper() -> dict[str, bool | list[int]]:
        pid_list: list[int] = []
        for proc in psutil.process_iter():
            try:
                for c in proc.cmdline():
                    if API_NAME in str(c) and "python" in str(proc.exe()):
                        pid_list.append(proc.pid)
                        break
            except psutil.AccessDenied:
                pass

        return {"success": True, "data": pid_list}

    return wrapper()
