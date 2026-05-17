"""Webcam sense plugin — OpenCV backend."""

import asyncio
import io
from typing import Any, AsyncIterator, Dict, List, Optional

from argus.config import get_config
from argus.senses.base import SenseData, SensePlugin


try:
    import cv2
    import numpy as np
    from PIL import Image
    _HAS_CV2 = True
except Exception:
    _HAS_CV2 = False


class WebcamPlugin(SensePlugin):
    name = "webcam"
    capabilities = ["capture", "stream", "detect"]

    def __init__(self) -> None:
        self._cap: Optional[Any] = None
        self._lock = asyncio.Lock()

    async def probe(self) -> bool:
        if not _HAS_CV2:
            return False
        # Try to open the default camera briefly
        cap = cv2.VideoCapture(get_config().webcam_device)
        ok = cap.isOpened()
        if ok:
            cap.release()
        return ok

    def _open(self) -> Any:
        cfg = get_config()
        cap = cv2.VideoCapture(cfg.webcam_device)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.webcam_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.webcam_height)
        cap.set(cv2.CAP_PROP_FPS, cfg.webcam_fps)
        return cap

    def _read_frame(self) -> Optional[Any]:
        if self._cap is None or not self._cap.isOpened():
            self._cap = self._open()
        ret, frame = self._cap.read()
        return frame if ret else None

    def _encode(self, frame: Any) -> bytes:
        cfg = get_config()
        # BGR -> RGB -> JPEG
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=cfg.jpeg_quality)
        return buf.getvalue()

    async def read(self) -> SenseData:
        async with self._lock:
            frame = await asyncio.to_thread(self._read_frame)
        if frame is None:
            return SenseData(sensor=self.name, error="Failed to capture frame")
        jpeg = await asyncio.to_thread(self._encode, frame)
        return SenseData(
            sensor=self.name,
            data={"width": frame.shape[1], "height": frame.shape[0]},
            image=jpeg,
            text=f"Captured {frame.shape[1]}x{frame.shape[0]} image from webcam",
        )

    async def stream(self) -> AsyncIterator[SenseData]:
        while True:
            yield await self.read()

    async def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def mcp_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "argus_webcam_capture",
                "description": "Capture a photo from the laptop webcam.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_webcam_capture":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
