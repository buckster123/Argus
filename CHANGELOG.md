# Changelog

## v0.2.0 — 2026-05-17

### Added
- **Test suite**: 29 tests covering all 4 universal sensors (webcam, audio, screen, system)
- **CI/CD**: GitHub Actions workflow for Python 3.10–3.13 with pytest + ruff
- **Dashboard UI**: Cyberpunk-themed HTML/CSS/JS with live sensor cards, SSE streaming, image previews
- **Hermes plugin**: `hermes-argus-plugin/` — dashboard tab + FastAPI backend proxying Argus API
- **USB plugin stubs**: thermal, environmental, GPS, serial co-processor — ready for community
- **Docs**: `docs/PLUGINS.md` contribution guide, `docs/API.md`, `docs/MCP.md`
- **`.hermes.md`**: AI-optimized context file for agent orientation

### Changed
- `argus-mcp` returns `ImageContent` for webcam/screen captures
- Dashboard serves static files from `argus/static/`
- Audio module exports `sd`/`np` even on import failure (fixes test mocking)

### Fixed
- Screen plugin graceful failure when `$DISPLAY` unset
- Webcam camera contention via async lock

## v0.1.0 — 2026-05-17

### Added
- Initial release with 4 universal sensors:
  - **Webcam** — OpenCV capture, stream, detect
  - **Audio** — sounddevice microphone recording
  - **Screen** — mss screenshot capture
  - **System** — psutil health (CPU, memory, disk, battery, temperature)
- MCP server with dynamic tool registration
- FastAPI dashboard with REST + SSE endpoints
- Plugin registry with auto-discovery
- `pyproject.toml` with optional deps per sensor tier
