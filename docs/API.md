# REST API Reference

Base URL: `http://localhost:8080`

## Status

### `GET /api/status`

List available sensors and their capabilities.

**Response:**
```json
{
  "available": [
    {"name": "webcam", "capabilities": ["capture", "stream", "detect"]},
    {"name": "system", "capabilities": ["capture", "stream"]}
  ],
  "all": {"webcam": true, "audio": false, "screen": true, "system": true}
}
```

## Sensor Operations

### `GET /api/{sensor}/read`

Read a single snapshot from a sensor.

**Response:** JSON `SenseData`
```json
{
  "sensor": "system",
  "timestamp": 1779033498.099,
  "data": {"cpu_percent": 5.0, "memory_percent": 50.0},
  "text": "CPU: 5.0%\nMemory: 50.0%",
  "error": null
}
```

### `GET /api/{sensor}/stream`

SSE stream of continuous readings.

**Headers:** `Content-Type: text/event-stream`

**Events:**
```
data: {"sensor": "system", "timestamp": ..., ...}

data: {"sensor": "system", "timestamp": ..., ...}
```

### `GET /api/{sensor}/image`

Direct JPEG image (if sensor produces images).

**Response:** `image/jpeg`

### `GET /api/{sensor}/audio`

Direct WAV audio (if sensor produces audio).

**Response:** `audio/wav`

## Dashboard

### `GET /`

Main dashboard UI (HTML).

### `GET /static/{path}`

Static assets (CSS, JS).
