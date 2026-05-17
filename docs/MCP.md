# MCP Tools Reference

Argus exposes one tool per sensor capability. Tools are dynamically registered — only sensors that `probe()` successfully get tools.

## Available Tools

### `argus_webcam_capture`

Capture a photo from the laptop webcam.

**Returns:**
- `TextContent` — dimensions and status
- `ImageContent` — base64 JPEG

### `argus_screen_capture`

Capture a screenshot of the primary monitor.

**Returns:**
- `TextContent` — dimensions and status
- `ImageContent` — base64 JPEG

### `argus_audio_capture`

Record audio from the laptop microphone.

**Arguments:**
- `duration_sec` (number, optional) — default 5.0

**Returns:**
- `TextContent` — duration and sample rate
- `TextContent` — base64 WAV data

### `argus_system_read`

Read laptop system health.

**Returns:**
- `TextContent` — human-readable summary (CPU, memory, disk, battery)
- `TextContent` — JSON data object

## Tool Naming Convention

`argus_{sensor_name}_{action}`

Examples:
- `argus_webcam_capture`
- `argus_system_read`
- `argus_usb_thermal_read` (stub — not yet active)

## Response Format

Success responses contain multiple `Content` items:

| Content Type | Condition |
|-------------|-----------|
| `TextContent` | Always — human-readable `.text` or error |
| `ImageContent` | If `.image` present (webcam, screen, thermal) |
| `TextContent` | If `.audio` present — base64 WAV note |
| `TextContent` | If `.data` present — JSON dump |

## Connecting

### Claude Code

```json
{
  "mcpServers": {
    "argus": {
      "command": "/path/to/venv/bin/argus-mcp"
    }
  }
}
```

### Hermes

```yaml
mcpServers:
  argus:
    command: /path/to/venv/bin/argus-mcp
```

### Direct Python

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(command="argus-mcp", args=[])
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("argus_webcam_capture", {})
```
