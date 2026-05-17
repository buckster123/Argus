# Argus v0.2.0 Implementation Plan

> **For Hermes:** Use subagent-driven-development + TDD skill to implement task-by-task.

**Goal:** Harden Argus v0.1.0 into a production-ready package: full test coverage, CI, Hermes dashboard plugin, USB plugin stubs, and comprehensive docs.

**Architecture:** Plugin-based sensor array with async probe/read/stream lifecycle. MCP server dynamically registers tools. FastAPI dashboard serves REST + SSE. All sensors implement `SensePlugin` ABC.

**Tech Stack:** Python 3.10+, pytest, pytest-asyncio, FastAPI, MCP SDK, OpenCV, mss, psutil, sounddevice.

---

## Phase 1: Infrastructure & Tooling (30 min)

**Why:** v0.1.0 has zero tests and no CI. Before adding features, we need guardrails.

**Tasks:**
1. Add pytest + pytest-asyncio + pytest-cov + ruff to dev deps
2. Create `pytest.ini` with asyncio_mode=auto
3. Add `.github/workflows/ci.yml` — lint + test on push/PR
4. Add `Makefile` with `make test`, `make lint`, `make run`
5. Create `.hermes.md` AI context file for the project
6. Commit

**Commit:** `chore: add test infrastructure, CI, linting`

---

## Phase 2: Core Plugin Tests (TDD) (45 min)

**Why:** Every sensor plugin needs verified probe/read behavior before we build on top.

**Order:** Write failing test → implement minimal pass → refactor → commit.

### 2a: Base plugin tests
- `tests/test_base.py`: `SenseData` dataclass behavior, timestamp generation

### 2b: System plugin tests
- `tests/test_system.py`: Mock `psutil` calls, verify `SenseData` shape, test battery/temp presence

### 2c: Screen plugin tests
- `tests/test_screen.py`: Mock `mss` grab, verify JPEG output, test failure when display unset

### 2d: Webcam plugin tests
- `tests/test_webcam.py`: Mock `cv2.VideoCapture`, verify probe/read/encode cycle

### 2e: Audio plugin tests
- `tests/test_audio.py`: Mock `sounddevice`/`sd.rec`, verify WAV output structure

### 2f: Plugin registry tests
- `tests/test_registry.py`: Test discovery with mock plugins, availability tracking

**Commit per plugin:** `test: add {sensor} plugin tests`

---

## Phase 3: Dashboard Polish & SSE (30 min)

**Why:** v0.1.0 dashboard is bare HTML. Needs responsive layout, dark theme polish, live sensor cards.

**Tasks:**
1. Extract inline HTML to `argus/static/index.html` + `argus/static/style.css`
2. Add auto-refresh sensor cards with fetch polling
3. Verify SSE stream endpoint works with EventSource
4. Add `/api/stream/all` multiplexed SSE (all sensors)
5. Commit

**Commit:** `feat: polish dashboard UI, add multiplexed SSE`

---

## Phase 4: Hermes Dashboard Plugin (45 min)

**Why:** The user explicitly wants this as a Hermes feature. The `hermes-dashboard-plugin` skill defines slot/tab pattern.

**Tasks:**
1. Read `hermes-dashboard-plugin` skill
2. Create `argus/hermes_plugin.py` — implements Hermes dashboard plugin interface
3. Add tab: "Senses" showing live sensor status with thumbnails
4. Add slot: "Argus" in the main dashboard showing recent captures
5. Document integration in README
6. Commit

**Commit:** `feat: add Hermes dashboard plugin integration`

---

## Phase 5: USB Plugin Ecosystem Stubs (30 min)

**Why:** Community needs extension points. Stubs = clear interface + empty implementations.

**Tasks:**
1. Create `argus/senses/usb_thermal.py` — FLIR Lepton/Seek stub
2. Create `argus/senses/usb_environmental.py` — BME680/688 via FT232H stub
3. Create `argus/senses/usb_gps.py` — u-blox NEO stub
4. Create `argus/senses/serial_coprocessor.py` — ESP32 serial bridge stub
5. Add `docs/PLUGINS.md` with contribution guide
6. Commit

**Commit:** `feat: add USB/serial plugin stubs for community extensions`

---

## Phase 6: Documentation & Release (30 min)

**Why:** Public repo needs solid docs for adoption.

**Tasks:**
1. Expand README with architecture diagram (ASCII or SVG)
2. Add `docs/ARCHITECTURE.md` — deep dive for contributors
3. Add `docs/API.md` — REST endpoint reference
4. Add `docs/MCP.md` — MCP tool reference
5. Add `CHANGELOG.md` with v0.1.0 and v0.2.0 sections
6. Bump version to 0.2.0 in `pyproject.toml` + `__init__.py`
7. Tag `v0.2.0` and push
8. Commit

**Commit:** `docs: comprehensive docs, bump v0.2.0`

---

## Time Estimates

| Phase | Time | Cumulative |
|-------|------|------------|
| 1. Infrastructure | 30 min | 30 min |
| 2. Plugin Tests | 45 min | 1h 15m |
| 3. Dashboard | 30 min | 1h 45m |
| 4. Hermes Plugin | 45 min | 2h 30m |
| 5. USB Stubs | 30 min | 3h |
| 6. Docs & Release | 30 min | 3h 30m |

**Total: ~3.5 hours** (can batch phases 1-2, 3-4, 5-6 across sessions)

---

## Acceptance Criteria

- [ ] `pytest` passes 100% (no skips)
- [ ] `ruff check` passes clean
- [ ] CI green on GitHub
- [ ] Dashboard renders at `localhost:8080` with live sensor cards
- [ ] MCP tools return correct ImageContent for webcam/screen
- [ ] Hermes plugin tab shows sensor thumbnails
- [ ] USB plugin stubs compile and probe() returns False gracefully
- [ ] README explains architecture in <5 min read
