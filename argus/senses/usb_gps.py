"""USB GPS plugin — u-blox NEO-6M/7M/8M, etc.

Requires: ``pip install pyserial pynmea2``

Hardware:
- u-blox NEO-6M/7M/8M USB GPS module (~$15) — USB serial, NMEA-0183
- GNSS modules with PPS output for timing applications
"""

from typing import Any, AsyncIterator, Dict, List

from argus.senses.base import SenseData, SensePlugin


try:
    import serial
    _HAS_GPS = True
except Exception:
    serial = None  # type: ignore
    _HAS_GPS = False


class UsbGpsPlugin(SensePlugin):
    """Stub for USB GPS support.

    TODO: Implement actual GPS backend:
    - Open /dev/ttyUSB* /dev/ttyACM* at 9600 baud
    - Parse NMEA-0183 sentences (GGA, RMC) via pynmea2
    - Return lat, lon, altitude, speed, fix quality, satellite count
    """

    name = "usb_gps"
    capabilities = ["capture", "stream"]

    def __init__(self) -> None:
        self._port: Any = None

    async def probe(self) -> bool:
        if not _HAS_GPS:
            return False

        # TODO: Scan serial ports for NMEA output
        return False

    async def read(self) -> SenseData:
        return SenseData(
            sensor=self.name,
            error="USB GPS not yet implemented. See argus/senses/usb_gps.py",
        )

    async def stream(self) -> AsyncIterator[SenseData]:
        while True:
            yield await self.read()

    async def close(self) -> None:
        if self._port is not None:
            self._port.close()
            self._port = None

    def mcp_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "argus_usb_gps_read",
                "description": "Read GPS location: latitude, longitude, altitude, speed.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_usb_gps_read":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
