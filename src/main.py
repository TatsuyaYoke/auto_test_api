from __future__ import annotations

from fastapi import FastAPI

import src.routers.bus

app = FastAPI()
app.include_router(src.routers.bus.router, prefix="/bus", tags=["bus"])


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
