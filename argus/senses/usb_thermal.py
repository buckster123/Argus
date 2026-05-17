"""USB thermal camera plugin — FLIR Lepton, Seek Thermal, generic UVC thermal.

Requires: ``pip install argus-senses[thermal]`` or manual install of:
- flirpy (FLIR Lepton)
- seekcamera (Seek Thermal)
- opencv-python (generic UVC thermal cameras)

Hardware:
- FLIR Lepton 3.5 (~$200) — 160x120, 8-14μm, via PureThermal breakout
- Seek Thermal Compact (~$200) — 206x156, micro-USB
- Generic UVC thermal cameras (~$50-100) — appear as webcams with false-color
"""

from typing import Any, AsyncIterator, Dict, List, Optional

from argus.config import get_config
from argus.senses.base import SenseData, SensePlugin


try:
    import cv2
    _HAS_THERMAL = True
except Exception:
    _HAS_THERMAL = False


class UsbThermalPlugin(SensePlugin):
    """Stub for USB thermal camera support.

    TODO: Implement actual thermal camera backends:
    - FLIR Lepton via flirpy/LeptonSDK
    - Seek Thermal via seekcamera SDK
    - Generic UVC thermal via OpenCV (false-color only)
    """

    name = "usb_thermal"
    capabilities = ["capture", "stream"]

    def __init__(self) -> None:
        self._cap: Optional[Any] = None
        self._backend: Optional[str] = None

    async def probe(self) -> bool:
        if not _HAS_THERMAL:
            return False

        # TODO: Auto-detect connected thermal camera
        # 1. Try FLIR Lepton via flirpy (I2C or USB)
        # 2. Try Seek Thermal via seekcamera SDK
        # 3. Try generic UVC thermal as /dev/videoN with thermal-specific VID:PID
        return False

    async def read(self) -> SenseData:
        # TODO: Read 16-bit thermal frame, convert to ironbow/JET colormap JPEG
        return SenseData(
            sensor=self.name,
            error="USB thermal camera not yet implemented. See argus/senses/usb_thermal.py",
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
                "name": "argus_usb_thermal_read",
                "description": "Read a thermal heatmap from a USB thermal camera.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_usb_thermal_read":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
