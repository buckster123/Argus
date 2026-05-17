"""Auto-discovers and manages Argus sensor plugins."""

import importlib
import inspect
import pkgutil
from typing import Dict, List, Type

from argus.senses.base import SensePlugin


class PluginRegistry:
    """Scans argus.senses.* for SensePlugin subclasses."""

    def __init__(self) -> None:
        self._plugins: Dict[str, SensePlugin] = {}
        self._available: Dict[str, bool] = {}

    async def discover(self) -> None:
        """Probe every built-in plugin; keep the ones that are present."""
        from argus import senses as senses_pkg

        plugin_classes: List[Type[SensePlugin]] = []

        # Walk argus.senses submodules
        for importer, modname, ispkg in pkgutil.iter_modules(senses_pkg.__path__, senses_pkg.__name__ + "."):
            if ispkg:
                continue
            try:
                mod = importlib.import_module(modname)
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if issubclass(obj, SensePlugin) and obj is not SensePlugin and not getattr(obj, "__abstractmethods__", None):
                        plugin_classes.append(obj)
            except Exception:
                continue  # Plugin deps missing = silently skip

        # Instantiate and probe
        for cls in plugin_classes:
            instance = cls()
            try:
                ok = await instance.probe()
                self._available[instance.name] = ok
                if ok:
                    self._plugins[instance.name] = instance
            except Exception:
                self._available[instance.name] = False

    def get(self, name: str) -> SensePlugin:
        return self._plugins[name]

    def list_available(self) -> List[str]:
        return [n for n, ok in self._available.items() if ok]

    def list_all(self) -> Dict[str, bool]:
        return dict(self._available)

    def all_plugins(self) -> Dict[str, SensePlugin]:
        return dict(self._plugins)

    async def close_all(self) -> None:
        for p in self._plugins.values():
            try:
                await p.close()
            except Exception:
                pass
