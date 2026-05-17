"""Tests for audio capture plugin."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from argus.senses.audio import AudioPlugin


class TestAudioPlugin:
    async def test_probe_success(self):
        mock_sd = MagicMock()
        mock_sd.query_devices.return_value = [{"name": "mic"}]
        with patch("argus.senses.audio.sd", mock_sd), patch("argus.senses.audio._HAS_AUDIO", True):
            p = AudioPlugin()
            assert await p.probe() is True

    async def test_probe_no_deps(self):
        with patch("argus.senses.audio._HAS_AUDIO", False):
            p = AudioPlugin()
            assert await p.probe() is False

    async def test_read_success(self):
        mock_sd = MagicMock()
        mock_np = MagicMock()
        fake_audio = np.zeros(80000, dtype=np.int16)
        mock_sd.rec.return_value = fake_audio
        with patch("argus.senses.audio.sd", mock_sd), patch("argus.senses.audio.np", mock_np), patch("argus.senses.audio._HAS_AUDIO", True):
            p = AudioPlugin()
            result = await p.read()

            assert result.sensor == "audio"
            assert result.error is None
            assert result.audio is not None
            assert len(result.audio) > 0
            assert result.data["sample_rate"] == 16000
            assert result.data["channels"] == 1

    async def test_read_failure(self):
        mock_sd = MagicMock()
        mock_sd.rec.side_effect = Exception("no mic")
        import numpy as real_np
        with patch("argus.senses.audio.sd", mock_sd), patch("argus.senses.audio.np", real_np), patch("argus.senses.audio._HAS_AUDIO", True):
            p = AudioPlugin()
            result = await p.read()
            assert result.sensor == "audio"
            assert result.error == "no mic"

    def test_mcp_tools(self):
        p = AudioPlugin()
        tools = p.mcp_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "argus_audio_capture"
        assert "duration_sec" in tools[0]["inputSchema"]["properties"]

    async def test_mcp_call_with_duration(self):
        mock_sd = MagicMock()
        fake_audio = np.zeros(16000, dtype=np.int16)  # 1 second
        mock_sd.rec.return_value = fake_audio
        import numpy as real_np
        with patch("argus.senses.audio.sd", mock_sd), patch("argus.senses.audio.np", real_np), patch("argus.senses.audio._HAS_AUDIO", True):
            p = AudioPlugin()
            result = await p.mcp_call("argus_audio_capture", {"duration_sec": 1.0})
            assert result.sensor == "audio"
            assert result.data["duration_sec"] == 1.0
