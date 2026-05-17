"""Screen capture sense plugin — MSS backend with Wayland-aware fallback."""

import asyncio
import io
import os
import subprocess
from typing import Any, Dict, List, Optional, Tuple, Union

from argus.config import get_config
from argus.senses.base import SenseData, SensePlugin


try:
    import mss
    from PIL import Image
    _HAS_MSS = True
except Exception:
    _HAS_MSS = False


def _is_wayland() -> bool:
    return os.environ.get("WAYLAND_DISPLAY", "") != "" or os.environ.get("XDG_SESSION_TYPE", "") == "wayland"


def _try_gnome_screenshot() -> Optional[Tuple[bytes, Tuple[int, int]]]:
    """Try GNOME Shell Screenshot DBus (GNOME on Wayland)."""
    try:
        path = "/tmp/argus_gnome_screenshot.png"
        result = subprocess.run(
            [
                "dbus-send", "--session", "--dest=org.gnome.Shell",
                "--type=method_call", "--print-reply", "--reply-timeout=10000",
                "/org/gnome/Shell/Screenshot", "org.gnome.Shell.Screenshot.Screenshot",
                "boolean:false", "boolean:false", f"string:{path}",
            ],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0 and os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            os.unlink(path)
            # Convert PNG to JPEG
            img = Image.open(io.BytesIO(data))  # type: ignore[possibly-unbound]
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=get_config().jpeg_quality)
            return buf.getvalue(), img.size
    except Exception:
        pass
    return None


def _is_black_image(img: "Image.Image") -> bool:
    """Check if a PIL image is essentially black/empty."""
    import numpy as np
    arr = np.array(img)
    return float(arr.mean()) < 5.0 and int(arr.max()) < 30


def _try_ffmpeg_x11() -> Optional[Tuple[bytes, Tuple[int, int]]]:
    """Try ffmpeg x11grab (works on XWayland with a visible X11 surface)."""
    try:
        display = os.environ.get("DISPLAY", ":0")
        path = "/tmp/argus_ffmpeg_screen.jpg"
        result = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-f", "x11grab", "-i", display, "-frames:v", "1",
                "-update", "1", "-y", path,
            ],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0 and os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            os.unlink(path)
            img = Image.open(io.BytesIO(data))  # type: ignore[possibly-unbound]
            if _is_black_image(img):
                return None  # XWayland surface is empty
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=get_config().jpeg_quality)
            return buf.getvalue(), img.size
    except Exception:
        pass
    return None


def _try_grim() -> Optional[Tuple[bytes, Tuple[int, int]]]:
    """Try grim (wlroots-based compositors)."""
    try:
        result = subprocess.run(
            ["grim", "-t", "jpeg", "-q", str(get_config().jpeg_quality), "-"],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout:
            img = Image.open(io.BytesIO(result.stdout))  # type: ignore[possibly-unbound]
            return result.stdout, img.size
    except Exception:
        pass
    return None


def _try_screenshot_tool() -> Optional[Tuple[bytes, Tuple[int, int]]]:
    """Try any installed screenshot CLI tool."""
    tools: List[Tuple[str, List[str]]] = [
        ("gnome-screenshot", ["gnome-screenshot", "-f", "/tmp/argus_tool.png"]),
        ("spectacle", ["spectacle", "-b", "-o", "/tmp/argus_tool.png"]),
        ("scrot", ["scrot", "/tmp/argus_tool.png"]),
        ("flameshot", ["flameshot", "gui", "--raw"]),
    ]
    for name, cmd in tools:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=15)
            if result.returncode == 0:
                if name == "flameshot":
                    data = result.stdout
                else:
                    path = "/tmp/argus_tool.png"
                    if not os.path.exists(path):
                        continue
                    with open(path, "rb") as f:
                        data = f.read()
                    os.unlink(path)
                img = Image.open(io.BytesIO(data))  # type: ignore[possibly-unbound]
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=get_config().jpeg_quality)
                return buf.getvalue(), img.size
        except Exception:
            continue
    return None


class ScreenPlugin(SensePlugin):
    name = "screen"
    capabilities = ["capture", "stream"]

    def __init__(self) -> None:
        self._sct = None

    async def probe(self) -> bool:
        if not _HAS_MSS:
            return False
        # On Wayland, MSS captures XWayland which is usually empty/black.
        # We still report available but warn in read().
        return True

    def _capture_mss(self) -> Tuple[bytes, Tuple[int, int]]:
        if self._sct is None:
            self._sct = mss.mss()
        cfg = get_config()
        monitor = self._sct.monitors[cfg.screen_monitor]
        raw = self._sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=cfg.jpeg_quality)
        return buf.getvalue(), img.size

    async def read(self) -> SenseData:
        if _is_wayland():
            # Try Wayland-compatible fallbacks in order
            for method_name, method in [
                ("grim", _try_grim),
                ("gnome-screenshot", _try_gnome_screenshot),
                ("ffmpeg x11grab", _try_ffmpeg_x11),
                ("screenshot tool", _try_screenshot_tool),
            ]:
                result = await asyncio.to_thread(method)
                if result:
                    jpeg, size = result
                    return SenseData(
                        sensor=self.name,
                        data={"width": size[0], "height": size[1], "method": method_name},
                        image=jpeg,
                        text=f"Captured {size[0]}x{size[1]} screenshot via {method_name}",
                    )
            return SenseData(
                sensor=self.name,
                error=(
                    "Screen capture unavailable on Wayland. "
                    "Install grim (wlroots), gnome-screenshot (GNOME), or spectacle (KDE). "
                    "Or run under X11 where MSS works natively."
                ),
            )

        try:
            jpeg, size = await asyncio.to_thread(self._capture_mss)
            return SenseData(
                sensor=self.name,
                data={"width": size[0], "height": size[1]},
                image=jpeg,
                text=f"Captured {size[0]}x{size[1]} screenshot of primary monitor",
            )
        except Exception as e:
            return SenseData(sensor=self.name, error=str(e))

    async def close(self) -> None:
        if self._sct is not None:
            self._sct.close()
            self._sct = None

    def mcp_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "argus_screen_capture",
                "description": "Capture a screenshot of the primary monitor.",
                "inputSchema": {"type": "object", "properties": {}},
            }
        ]

    async def mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> SenseData:
        if tool_name == "argus_screen_capture":
            return await self.read()
        return await super().mcp_call(tool_name, arguments)