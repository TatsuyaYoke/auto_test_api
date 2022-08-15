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
app.include_router(src.routers.trans.router, prefix="/trans", tags=["trans"])


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
