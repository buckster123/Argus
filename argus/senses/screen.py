"""Screen capture sense plugin — MSS backend."""

import asyncio
import io
from typing import Any, Dict, List

from argus.config import get_config
from argus.senses.base import SenseData, SensePlugin


try:
    import mss
    from PIL import Image
    _HAS_MSS = True
except Exception:
    _HAS_MSS = False


class ScreenPlugin(SensePlugin):
    name = "screen"
    capabilities = ["capture", "stream"]

    def __init__(self) -> None:
        self._sct = None

    async def probe(self) -> bool:
        return _HAS_MSS

    def _capture(self) -> bytes:
        if self._sct is None:
            self._sct = mss.mss()
        cfg = get_config()
        monitor = self._sct.monitors[cfg.screen_monitor]
        raw = self._sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=cfg.jpeg_quality)
        return buf.getvalue(), img.size

    async def read(self) -> SenseData:
        try:
            jpeg, size = await asyncio.to_thread(self._capture)
            return SenseData(
                sensor=self.name,
                data={"width": size[0], "height": size[1]},
                image=jpeg,
                text=f"Captured {size[0]}x{size[1]} screenshot of primary monitor",
            )
        except Exception as e:
            return SenseData(sensor=self.name, error=str(e))

    async def close(self) -> None:
        if self._sct is not None:
            self._sct.close()
            self._sct = None

    def mcp_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "argus_screen_capture",
                "description": "Capture a screenshot of the primary monitor.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_screen_capture":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
