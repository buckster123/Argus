"""System health sense plugin — psutil backend."""

import asyncio
import time
from typing import Any, AsyncIterator, Dict, List

from argus.config import get_config
from argus.senses.base import SenseData, SensePlugin


try:
    import psutil
    _HAS_PSUTIL = True
except Exception:
    _HAS_PSUTIL = False


class SystemPlugin(SensePlugin):
    name = "system"
    capabilities = ["capture", "stream"]

    async def probe(self) -> bool:
        return _HAS_PSUTIL

    def _read(self) -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        data: Dict[str, Any] = {
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "memory_total_mb": round(mem.total / (1024 * 1024), 1),
            "memory_used_mb": round(mem.used / (1024 * 1024), 1),
            "memory_percent": mem.percent,
            "disk_total_gb": round(disk.total / (1024 ** 3), 1),
            "disk_used_gb": round(disk.used / (1024 ** 3), 1),
            "disk_percent": round(disk.used / disk.total * 100, 1),
            "net_sent_mb": round(net.bytes_sent / (1024 * 1024), 2),
            "net_recv_mb": round(net.bytes_recv / (1024 * 1024), 2),
        }

        # Battery (laptops)
        if hasattr(psutil, "sensors_battery"):
            batt = psutil.sensors_battery()
            if batt is not None:
                data["battery_percent"] = batt.percent
                data["battery_plugged"] = batt.power_plugged
                data["battery_secs_left"] = batt.secsleft if batt.secsleft != -2 else None

        # Temperature sensors (Linux mostly)
        temps = {}
        if hasattr(psutil, "sensors_temperatures"):
            for name, entries in psutil.sensors_temperatures().items():
                for entry in entries:
                    if entry.current is not None:
                        temps.setdefault(name, {})[entry.label or "core"] = entry.current
        if temps:
            data["temperatures_c"] = temps

        return data

    async def read(self) -> SenseData:
        try:
            data = await asyncio.to_thread(self._read)
            lines = [
                f"CPU: {data['cpu_percent']}%",
                f"Memory: {data['memory_percent']}% used ({data['memory_used_mb']} / {data['memory_total_mb']} MB)",
                f"Disk: {data['disk_percent']}% used ({data['disk_used_gb']} / {data['disk_total_gb']} GB)",
            ]
            if "battery_percent" in data:
                lines.append(f"Battery: {data['battery_percent']}% {'(plugged)' if data['battery_plugged'] else '(discharging)'}")
            return SenseData(
                sensor=self.name,
                data=data,
                text="\n".join(lines),
            )
        except Exception as e:
            return SenseData(sensor=self.name, error=str(e))

    async def stream(self) -> AsyncIterator[SenseData]:
        while True:
            yield await self.read()
            await asyncio.sleep(get_config().system_poll_interval)

    def mcp_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "argus_system_read",
                "description": "Read laptop system health: CPU, memory, disk, battery, temperature.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_system_read":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)
