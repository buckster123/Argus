"""Argus FastAPI dashboard — REST + SSE streaming."""

import asyncio
import base64
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, Response
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
    return """<!DOCTYPE html>
<html>
<head>
    <title>Argus Dashboard</title>
    <style>
        body { font-family: system-ui, sans-serif; background:#0b0c10; color:#c5c6c7; margin:0; padding:2rem; }
        h1 { color:#66fcf1; }
        .sensor { background:#1f2833; border-radius:8px; padding:1rem; margin:1rem 0; }
        .sensor h2 { margin-top:0; color:#45a29e; }
        .caps span { background:#0b0c10; padding:.2rem .6rem; border-radius:4px; margin-right:.4rem; font-size:.8rem; }
        a { color:#66fcf1; }
        pre { background:#0b0c10; padding:1rem; overflow:auto; }
    </style>
</head>
<body>
    <h1>Argus — Agent Senses</h1>
    <div id="sensors">Loading...</div>
    <script>
        async function load() {
            const r = await fetch('/api/status');
            const j = await r.json();
            const div = document.getElementById('sensors');
            div.innerHTML = '';
            for (const s of j.available) {
                div.innerHTML += `<div class="sensor">
                    <h2>${s.name}</h2>
                    <div class="caps">${s.capabilities.map(c=>`<span>${c}</span>`).join('')}</div>
                    <p><a href="/api/${s.name}/read">Read snapshot</a>
                    ${s.capabilities.includes('stream') ? ` | <a href="/api/${s.name}/stream">SSE stream</a>` : ''}
                    ${s.capabilities.includes('capture') ? ` | <a href="/api/${s.name}/image">Image</a>` : ''}</p>
                </div>`;
            }
        }
        load();
    </script>
</body>
</html>"""


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


def _sense_to_json(data: SenseData) -> str:
    import json
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
    return json.dumps(payload, default=str)


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
