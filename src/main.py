from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import src.routers.bus

app = FastAPI()

origins = [
  "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(src.routers.bus.router, prefix="/bus", tags=["bus"])


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}
