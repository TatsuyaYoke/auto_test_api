from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/hello")
async def obs_hello() -> dict[str, str]:
    return {"Hello": "trans"}
