"""Audio capture sense plugin — sounddevice backend."""

import asyncio
import io
import wave
from typing import Any, AsyncIterator, Dict, List, Optional

from argus.config import get_config
from argus.senses.base import SenseData, SensePlugin


try:
    import sounddevice as sd
    import numpy as np
    _HAS_AUDIO = True
except Exception:
    _HAS_AUDIO = False


class AudioPlugin(SensePlugin):
    name = "audio"
    capabilities = ["capture", "stream"]

    def __init__(self) -> None:
        self._stream: Optional[Any] = None

    async def probe(self) -> bool:
        if not _HAS_AUDIO:
            return False
        try:
            devices = sd.query_devices()
            return len(devices) > 0
        except Exception:
            return False

    def _record(self) -> bytes:
        cfg = get_config()
        frames = int(cfg.audio_sample_rate * cfg.audio_duration_sec)
        recording = sd.rec(
            frames,
            samplerate=cfg.audio_sample_rate,
            channels=cfg.audio_channels,
            dtype=np.int16,
            device=cfg.audio_device,
        )
        sd.wait()
        # Pack into WAV
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(cfg.audio_channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(cfg.audio_sample_rate)
            wf.writeframes(recording.tobytes())
        return buf.getvalue()

    async def read(self) -> SenseData:
        try:
            wav = await asyncio.to_thread(self._record)
            cfg = get_config()
            return SenseData(
                sensor=self.name,
                data={
                    "duration_sec": cfg.audio_duration_sec,
                    "sample_rate": cfg.audio_sample_rate,
                    "channels": cfg.audio_channels,
                },
                audio=wav,
                text=f"Recorded {cfg.audio_duration_sec}s of audio at {cfg.audio_sample_rate} Hz",
            )
        except Exception as e:
            return SenseData(sensor=self.name, error=str(e))

    async def stream(self) -> AsyncIterator[SenseData]:
        while True:
            yield await self.read()

    async def close(self) -> None:
        pass

    def mcp_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "argus_audio_capture",
                "description": "Record a short audio clip from the laptop microphone.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "duration_sec": {
                            "type": "number",
                            "description": "How many seconds to record (default 5)",
                        }
                    },
                },
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_audio_capture":
            # Temporarily override duration if requested
            duration = arguments.get("duration_sec")
            if duration is not None:
                cfg = get_config()
                old = cfg.audio_duration_sec
                cfg.audio_duration_sec = float(duration)
                try:
                    return await self.read()
                finally:
                    cfg.audio_duration_sec = old
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
