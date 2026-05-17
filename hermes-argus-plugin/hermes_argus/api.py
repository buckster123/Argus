"""FastAPI router for Hermes Argus dashboard plugin."""

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter()

ARGUS_URL = "http://localhost:8080"


@router.get("/status")
async def argus_status():
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{ARGUS_URL}/api/status", timeout=5.0)
            return r.json()
        except Exception:
            raise HTTPException(status_code=503, detail="Argus not running on :8080")


@router.get("/sensor/{name}/read")
async def sensor_read(name: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{ARGUS_URL}/api/{name}/read", timeout=10.0)
            return r.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/sensor/{name}/image")
async def sensor_image(name: str):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{ARGUS_URL}/api/{name}/image", timeout=10.0)
            return Response(content=r.content, media_type="image/jpeg")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
