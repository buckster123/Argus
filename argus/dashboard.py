"""Argus FastAPI dashboard — REST + SSE streaming."""

import asyncio
import base64
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from argus.config import get_config
from argus.plugin_registry import PluginRegistry
from argus.senses.base import SenseData


_registry: PluginRegistry | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _registry
    _registry = PluginRegistry()
    await _registry.discover()
    get_config().ensure_dirs()
    yield
    await _registry.close_all()


app = FastAPI(title="Argus Dashboard", version="0.1.0", lifespan=lifespan)

# Static files (dashboard UI)
import os
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        with open(index_path) as f:
            return f.read()
    return "<h1>Argus Dashboard</h1><p>Static files not found.</p>"


@app.get("/api/status")
async def api_status():
    reg = _registry
    if reg is None:
        raise HTTPException(status_code=503, detail="Registry not ready")
    available = []
    for name, plugin in reg.all_plugins().items():
        available.append({"name": name, "capabilities": plugin.capabilities})
    return {"available": available, "all": reg.list_all()}


@app.get("/api/{sensor}/read")
async def api_read(sensor: str):
    reg = _registry
    if reg is None or sensor not in reg.all_plugins():
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor}' not available")
    data = await reg.get(sensor).read()
    return _sense_to_json(data)


@app.get("/api/{sensor}/stream")
async def api_stream(sensor: str):
    reg = _registry
    if reg is None or sensor not in reg.all_plugins():
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor}' not available")
    if "stream" not in reg.get(sensor).capabilities:
        raise HTTPException(status_code=400, detail=f"Sensor '{sensor}' does not support streaming")

    async def event_stream() -> AsyncIterator[str]:
        async for data in reg.get(sensor).stream():
            yield f"data: {_sense_to_json(data)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/{sensor}/image")
async def api_image(sensor: str):
    reg = _registry
    if reg is None or sensor not in reg.all_plugins():
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor}' not available")
    data = await reg.get(sensor).read()
    if data.image:
        return Response(content=data.image, media_type="image/jpeg")
    if data.error:
        raise HTTPException(status_code=500, detail=data.error)
    raise HTTPException(status_code=400, detail="No image from this sensor")


@app.get("/api/{sensor}/audio")
async def api_audio(sensor: str):
    reg = _registry
    if reg is None or sensor not in reg.all_plugins():
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor}' not available")
    data = await reg.get(sensor).read()
    if data.audio:
        return Response(content=data.audio, media_type="audio/wav")
    if data.error:
        raise HTTPException(status_code=500, detail=data.error)
    raise HTTPException(status_code=400, detail="No audio from this sensor")


def _sense_to_json(data: SenseData) -> dict:
    payload = {
        "sensor": data.sensor,
        "timestamp": data.timestamp,
        "data": data.data,
        "text": data.text,
        "error": data.error,
    }
    if data.image:
        payload["image_b64"] = base64.b64encode(data.image).decode("utf-8")
    if data.audio:
        payload["audio_b64"] = base64.b64encode(data.audio).decode("utf-8")
    return payload


def main() -> None:
    import uvicorn
    cfg = get_config()
    uvicorn.run(
        "argus.dashboard:app",
        host=cfg.dashboard_host,
        port=cfg.dashboard_port,
        reload=cfg.dashboard_reload,
    )


if __name__ == "__main__":
    main()
