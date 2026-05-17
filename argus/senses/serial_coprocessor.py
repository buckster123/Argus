"""Serial co-processor plugin — ESP32, Arduino, RP2040 sensor bridges.

This plugin connects to a microcontroller running custom firmware that
aggregates I2C/SPI sensors and streams them over USB serial. It is the
bridge between Argus (laptop) and SensorHead (Pi/ESP hardware).

Protocol (JSON lines over serial):
  {"sensor": "bme688", "data": {"iaq": 123, "temp": 22.5, ...}}
  {"sensor": "mlx90640", "data": {"grid": [...], "min": 20.0, "max": 35.0}}

Requires: ``pip install pyserial``

Hardware:
- ESP32 + BME688 "nose" (~$15) — your existing SensorHead nose
- RP2040 + Qwiic sensor chain (~$10) — STEMMA QT ecosystem
- Arduino Nano 33 BLE Sense (~$30) — built-in IMU, mic, env sensor
"""

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List

from argus.senses.base import SenseData, SensePlugin


try:
    import serial
    import serial.tools.list_ports
    _HAS_SERIAL = True
except Exception:
    serial = None  # type: ignore
    _HAS_SERIAL = False


class SerialCoprocessorPlugin(SensePlugin):
    """Stub for serial co-processor support.

    TODO: Implement:
    - Auto-detect USB serial ports with specific VID:PID (e.g. 10C4:EA60 CP2102)
    - Send probe command, expect JSON handshake
    - Stream JSON lines, parse into SenseData
    - Support multiple virtual sensors multiplexed on one serial link
    """

    name = "serial_coprocessor"
    capabilities = ["capture", "stream"]

    def __init__(self) -> None:
        self._port: Any = None
        self._sensors: List[str] = []

    async def probe(self) -> bool:
        if not _HAS_SERIAL:
            return False

        # TODO: Scan serial ports and send {"cmd": "probe"}\n
        # Example scan:
        # for p in serial.tools.list_ports.comports():
        #     if p.vid == 0x10C4 and p.pid == 0xEA60:  # CP2102
        #         try port, send probe, check response
        return False

    async def read(self) -> SenseData:
        return SenseData(
            sensor=self.name,
            error="Serial co-processor not yet implemented. See argus/senses/serial_coprocessor.py",
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
                "name": "argus_serial_coprocessor_read",
                "description": "Read sensors attached to a USB serial co-processor (ESP32/Arduino).",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_serial_coprocessor_read":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
