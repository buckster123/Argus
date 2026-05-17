# 👁️ Argus

> **Physical senses for AI agents** — give your laptop eyes, ears, and awareness of itself. No extra hardware required.

---

## What Is This?

AI agents are brilliant. But they're usually locked inside a terminal, blind to the world around them.

**Argus fixes that.**

This is an MCP-connected sensor array that plugs real-world perception directly into any AI agent session. Point your laptop webcam at something. Ask your agent what it sees. Let it hear the room. Let it read its own system health. All through a clean, discoverable plugin architecture.

It's senses. For your agent. On any laptop.

---

## Architecture

```
Hermes / Claude / Any MCP Client
        |
        v
    argus-mcp              <- MCP server, stdio transport
        |
        v
    Argus Dashboard        <- FastAPI, port 8080
        |
   +----+----+--------+
   v    v    v        v
Webcam Audio Screen System
```

The MCP server talks to the dashboard over localhost REST. The agent calls tools; tools call sensors; sensors return data. Simple, fast, composable.

**Plugin architecture:**

```
PluginRegistry.discover()
    |
    +-- argus.senses.webcam    -> WebcamPlugin
    +-- argus.senses.audio     -> AudioPlugin
    +-- argus.senses.screen    -> ScreenPlugin
    +-- argus.senses.system    -> SystemPlugin
    +-- argus.senses.usb_thermal        (stub)
    +-- argus.senses.usb_environmental  (stub)
    +-- argus.senses.usb_gps            (stub)
    +-- argus.senses.serial_coprocessor (stub)
```

---

## Built-In Sensors (Universal Tier)

| Sense | What It Does | Library |
|-------|--------------|---------|
| 👁️ **Webcam** | Capture photos, stream video | OpenCV |
| 🎤 **Audio** | Record microphone clips | sounddevice |
| 🖥️ **Screen** | Screenshot the primary monitor | mss |
| 🧠 **System** | CPU, memory, disk, battery, temperature | psutil |

All four work on any modern laptop with zero configuration.

---

## Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/buckster123/Argus.git
cd Argus
python -m venv venv
source venv/bin/activate
pip install -e ".[audio]"
```

### 2. Start the Dashboard

```bash
argus-dashboard
# or
python -m argus
```

Open http://localhost:8080 to see your available sensors.

### 3. Connect to an MCP Client

Add to your Hermes / Claude / MCP client config:

```json
{
  "mcpServers": {
    "argus": {
      "command": "/path/to/Argus/venv/bin/argus-mcp"
    }
  }
}
```

Then just ask:

> *"What do you see right now?"*
> *"Take a screenshot and describe it."*
> *"How's my laptop doing?"*
> *"Record 5 seconds of audio."*

---

## REST API

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | List available sensors and capabilities |
| `GET /api/{sensor}/read` | Single snapshot (JSON) |
| `GET /api/{sensor}/stream` | SSE live stream |
| `GET /api/{sensor}/image` | Direct JPEG (if sensor has image) |
| `GET /api/{sensor}/audio` | Direct WAV (if sensor has audio) |

---

## Plugin Architecture

Argus is built around a simple plugin system. Every sensor implements:

```python
class SensePlugin(ABC):
    name: str
    capabilities: list[str]

    async def probe(self) -> bool: ...
    async def read(self) -> SenseData: ...
    async def stream(self) -> AsyncIterator[SenseData]: ...
    async def close(self): ...
```

Plugins auto-register. The scanner probes each one at startup and only exposes the sensors that are actually present.

### Future Tiers

| Tier | Examples | Status |
|------|----------|--------|
| **USB Thermal** | FLIR Lepton, Seek Thermal | Planned |
| **USB Environmental** | BME680/688 via FT232H | Planned |
| **USB GPS** | u-blox NEO | Planned |
| **Serial Co-processor** | ESP32 "nose" from SensorHead | Planned |
| **Bluetooth** | BLE temp/humidity sensors | Planned |

---

## Project Structure

```
Argus/
├── argus/
│   ├── senses/
│   │   ├── base.py      # Abstract plugin
│   │   ├── webcam.py    # OpenCV camera
│   │   ├── audio.py     # sounddevice mic
│   │   ├── screen.py    # mss screenshot
│   │   └── system.py    # psutil health
│   ├── plugin_registry.py
│   ├── mcp_server.py
│   ├── dashboard.py
│   └── config.py
├── tests/
├── pyproject.toml
└── README.md
```

---

## Requirements

- Python 3.10+
- Linux / macOS / Windows
- A webcam (built-in or USB)
- Optional: microphone, multi-monitor setup

---

## License

MIT — build weird things with it.

---

*Part of the [ApexAurum](https://github.com/buckster123) ecosystem — AI agents that live in the physical world.*
