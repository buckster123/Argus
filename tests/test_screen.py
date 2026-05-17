"""Tests for screen capture plugin."""

import pytest
from unittest.mock import MagicMock, patch

from argus.senses.screen import ScreenPlugin


class TestScreenPlugin:
    async def test_probe_with_mss(self):
        with patch("argus.senses.screen._HAS_MSS", True):
            p = ScreenPlugin()
            assert await p.probe() is True

    async def test_probe_without_mss(self):
        with patch("argus.senses.screen._HAS_MSS", False):
            p = ScreenPlugin()
            assert await p.probe() is False

    @patch("argus.senses.screen.mss.mss")
    async def test_read_success(self, mock_mss_factory):
        mock_sct = MagicMock()
        mock_sct.monitors = [{}, {"left": 0, "top": 0, "width": 1920, "height": 1080}]
        mock_sct.grab.return_value = MagicMock(
            size=(1920, 1080),
            bgra=b"\x00" * (1920 * 1080 * 4),
        )
        mock_mss_factory.return_value = mock_sct

        p = ScreenPlugin()
        result = await p.read()

        assert result.sensor == "screen"
        assert result.error is None
        assert result.image is not None
        assert len(result.image) > 0
        assert "1920x1080" in result.text

    @patch("argus.senses.screen.mss.mss", side_effect=Exception("no display"))
    async def test_read_failure(self, mock_mss):
        p = ScreenPlugin()
        result = await p.read()
        assert result.sensor == "screen"
        assert result.error == "no display"

    @patch("argus.senses.screen.mss.mss")
    async def test_close(self, mock_mss_factory):
        mock_sct = MagicMock()
        mock_mss_factory.return_value = mock_sct

        p = ScreenPlugin()
        # Trigger lazy init
        p._sct = mock_sct
        await p.close()
        mock_sct.close.assert_called_once()
        assert p._sct is None
