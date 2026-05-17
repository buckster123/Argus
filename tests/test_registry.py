"""Tests for PluginRegistry auto-discovery."""

import pytest
from unittest.mock import AsyncMock

from argus.plugin_registry import PluginRegistry
from argus.senses.base import SenseData, SensePlugin


class AlwaysAvailable(SensePlugin):
    name = "always"
    capabilities = ["capture"]

    async def probe(self):
        return True

    async def read(self):
        return SenseData(sensor=self.name)


class NeverAvailable(SensePlugin):
    name = "never"
    capabilities = []

    async def probe(self):
        return False

    async def read(self):
        return SenseData(sensor=self.name)


class BrokenProbe(SensePlugin):
    name = "broken"
    capabilities = []

    async def probe(self):
        raise RuntimeError("boom")

    async def read(self):
        return SenseData(sensor=self.name)


class TestPluginRegistry:
    async def test_empty_registry(self):
        reg = PluginRegistry()
        assert reg.list_available() == []
        assert reg.list_all() == {}

    async def test_manual_register_and_probe(self):
        reg = PluginRegistry()
        # Manually inject plugins (simulate discovery)
        reg._available["always"] = True
        reg._plugins["always"] = AlwaysAvailable()

        assert reg.list_available() == ["always"]
        assert reg.list_all() == {"always": True}

        plugin = reg.get("always")
        assert plugin.name == "always"

    async def test_close_all(self):
        reg = PluginRegistry()
        reg._plugins["always"] = AlwaysAvailable()
        await reg.close_all()
        # Should not raise

    async def test_get_missing_raises(self):
        reg = PluginRegistry()
        with pytest.raises(KeyError):
            reg.get("missing")
