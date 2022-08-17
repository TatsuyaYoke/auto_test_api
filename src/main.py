from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import src.routers.bus
import src.routers.obs
import src.routers.trans

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
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
