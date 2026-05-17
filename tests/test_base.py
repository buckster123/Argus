"""Tests for SensePlugin base class and SenseData."""

import time
from argus.senses.base import SenseData, SensePlugin


class DummyPlugin(SensePlugin):
    name = "dummy"
    capabilities = ["capture"]

    async def probe(self):
        return True

    async def read(self):
        return SenseData(sensor=self.name, text="hello")


class TestSenseData:
    def test_defaults(self):
        d = SenseData(sensor="test")
        assert d.sensor == "test"
        assert d.data == {}
        assert d.image is None
        assert d.audio is None
        assert d.text is None
        assert d.error is None
        assert abs(d.timestamp - time.time()) < 1

    def test_full_construction(self):
        d = SenseData(
            sensor="cam",
            data={"w": 100},
            image=b"jpeg",
            text="ok",
        )
        assert d.data == {"w": 100}
        assert d.image == b"jpeg"
        assert d.text == "ok"


class TestSensePlugin:
    def test_mcp_tools_default(self):
        p = DummyPlugin()
        tools = p.mcp_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "argus_dummy_read"

    def test_mcp_call_read(self):
        p = DummyPlugin()
        import asyncio
        result = asyncio.run(p.mcp_call("argus_dummy_read", {}))
        assert result.sensor == "dummy"
        assert result.text == "hello"

    def test_mcp_call_unknown(self):
        p = DummyPlugin()
        import asyncio
        import pytest
        with pytest.raises(ValueError):
            asyncio.run(p.mcp_call("argus_dummy_foo", {}))
