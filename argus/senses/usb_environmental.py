"""USB environmental sensor plugin — BME680/688, SCD4x, SPS30, etc.

Requires: ``pip install adafruit-circuitpython-bme680 pyserial``

Hardware:
- BME680/BME688 via FT232H USB-I2C bridge (~$20) — temp, humidity, pressure, VOC
- SCD4x via Qwiic/STEMMA QT USB bridge (~$30) — CO₂, temp, RH
- SPS30 via USB-I2C bridge (~$40) — particulate matter
- Your existing ESP32+BME688 "nose" over USB serial
"""

from typing import Any, AsyncIterator, Dict, List

from argus.senses.base import SenseData, SensePlugin


try:
    import serial
    _HAS_SERIAL = True
except Exception:
    serial = None  # type: ignore
    _HAS_SERIAL = False


class UsbEnvironmentalPlugin(SensePlugin):
    """Stub for USB environmental sensor support.

    TODO: Implement actual sensor backends:
    - BME680/688 via FT232H/Qwiic USB bridge (adafruit_bme680)
    - SCD4x CO2 sensor via USB bridge
    - SPS30 particulate sensor
    - ESP32 serial co-processor running SensorHead firmware
    """

    name = "usb_environmental"
    capabilities = ["capture", "stream"]

    def __init__(self) -> None:
        self._port: Any = None

    async def probe(self) -> bool:
        if not _HAS_SERIAL:
            return False

        # TODO: Scan /dev/ttyUSB* /dev/ttyACM* /dev/cu.* for known VID:PID pairs
        # TODO: Send probe command to ESP32 co-processor or scan I2C bus via FT232H
        return False

    async def read(self) -> SenseData:
        # TODO: Read BSEC2-compensated values or raw sensor data
        return SenseData(
            sensor=self.name,
            error="USB environmental sensor not yet implemented. See argus/senses/usb_environmental.py",
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
                "name": "argus_usb_environmental_read",
                "description": "Read environmental data: temperature, humidity, pressure, VOC, CO₂, PM2.5.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_usb_environmental_read":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
