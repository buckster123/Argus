"""Configuration for Argus."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ArgusConfig:
    """All tunables for Argus."""

    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8080
    dashboard_reload: bool = False

    # Webcam
    webcam_device: int = 0
    webcam_width: int = 1280
    webcam_height: int = 720
    webcam_fps: int = 30
    jpeg_quality: int = 85

    # Audio
    audio_sample_rate: int = 16000
    audio_channels: int = 1
    audio_duration_sec: float = 5.0
    audio_device: Optional[int] = None

    # Screen
    screen_monitor: int = 0  # 0 = primary

    # System
    system_poll_interval: float = 2.0

    # Plugin discovery
    extra_plugin_paths: list[str] = field(default_factory=list)

    # Data / cache
    data_dir: str = field(default_factory=lambda: str(Path.home() / ".argus" / "data"))
    cache_dir: str = field(default_factory=lambda: str(Path.home() / ".argus" / "cache"))

    def ensure_dirs(self) -> None:
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)


# Global singleton — mutated by CLI entry points
_config = ArgusConfig()


def get_config() -> ArgusConfig:
    return _config


def set_config(cfg: ArgusConfig) -> None:
    global _config
    _config = cfg
