# Argus Plugin Development Guide

Argus uses a simple plugin architecture. Every sensor is a plugin. You can add new sensors by creating a single Python file.

## Quick Start

1. Create `argus/senses/my_sensor.py`
2. Subclass `SensePlugin`
3. Implement `probe()`, `read()`, and optionally `stream()`
4. Restart Argus — it auto-discovers

## Minimal Example

```python
# argus/senses/my_sensor.py
from argus.senses.base import SenseData, SensePlugin

class MySensorPlugin(SensePlugin):
    name = "my_sensor"
    capabilities = ["capture"]

    async def probe(self) -> bool:
        # Return True if this sensor is available
        return True

    async def read(self) -> SenseData:
        return SenseData(
            sensor=self.name,
            data={"value": 42},
            text="The answer is 42",
        )
```

No registration needed. `PluginRegistry.discover()` finds it automatically.

## SensePlugin Interface

```python
class SensePlugin(ABC):
    name: str                    # Unique sensor identifier
    capabilities: list[str]      # ["capture", "stream", "detect"]

    async def probe(self) -> bool: ...
    async def read(self) -> SenseData: ...
    async def stream(self) -> AsyncIterator[SenseData]: ...
    async def close(self) -> None: ...
```

### probe()

Must return `True` if the sensor hardware is available. Should be fast (< 1s) and not leave handles open.

### read()

Return a `SenseData` snapshot. All fields are optional:

| Field | Type | Purpose |
|-------|------|---------|
| `sensor` | str | Sensor name (required) |
| `timestamp` | float | Unix timestamp (auto-filled) |
| `data` | dict | Raw sensor data (numbers, arrays, metadata) |
| `image` | bytes | JPEG or PNG bytes |
| `audio` | bytes | WAV bytes |
| `text` | str | Human-readable summary |
| `error` | str | Error message if read failed |

### stream()

Default implementation yields `read()` in a loop. Override for efficient continuous streaming (e.g., video frames).

### close()

Release hardware handles. Called on shutdown.

## MCP Integration

Override `mcp_tools()` to expose custom tools:

```python
def mcp_tools(self) -> list[dict]:
    return [
        {
            "name": "argus_my_sensor_read",
            "description": "Read from my sensor",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "resolution": {"type": "string", "enum": ["low", "high"]}
                }
            },
        }
    ]

async def mcp_call(self, tool_name: str, arguments: dict) -> SenseData:
    if tool_name == "argus_my_sensor_read":
        resolution = arguments.get("resolution", "low")
        return await self.read(resolution=resolution)
    return await super().mcp_call(tool_name, arguments)
```

## Testing Your Plugin

```python
# tests/test_my_sensor.py
import pytest
from argus.senses.my_sensor import MySensorPlugin

class TestMySensor:
    async def test_probe(self):
        p = MySensorPlugin()
        assert await p.probe() is True

    async def test_read(self):
        p = MySensorPlugin()
        result = await p.read()
        assert result.sensor == "my_sensor"
        assert result.data["value"] == 42
```

## Plugin Tiers

| Tier | Examples | Difficulty |
|------|----------|------------|
| **Universal** | Webcam, audio, screen, system | ⭐ — Built-in |
| **USB Plug** | Thermal, environmental, GPS | ⭐⭐ — USB vendor libs |
| **Serial** | ESP32 co-processor | ⭐⭐ — Custom protocol |
| **Bluetooth** | BLE sensors | ⭐⭐⭐ — BLE stack |
| **Custom** | Your hardware | ⭐⭐⭐ — Full implementation |

## Contributing

1. Fork the repo
2. Add your plugin under `argus/senses/`
3. Add tests under `tests/`
4. Update README with hardware requirements
5. Submit a PR

See the existing stubs for reference:
- `argus/senses/usb_thermal.py`
- `argus/senses/usb_environmental.py`
- `argus/senses/usb_gps.py`
- `argus/senses/serial_coprocessor.py`
