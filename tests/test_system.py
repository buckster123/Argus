"""Tests for system health plugin."""

import pytest
from unittest.mock import MagicMock, patch

from argus.senses.system import SystemPlugin


class TestSystemPlugin:
    @patch("argus.senses.system.psutil")
    async def test_probe(self, mock_psutil):
        p = SystemPlugin()
        assert await p.probe() is True

    @patch("argus.senses.system.psutil.cpu_percent", return_value=5.0)
    @patch("argus.senses.system.psutil.cpu_count", return_value=8)
    @patch("argus.senses.system.psutil.virtual_memory")
    @patch("argus.senses.system.psutil.disk_usage")
    @patch("argus.senses.system.psutil.net_io_counters")
    @patch("argus.senses.system.psutil.sensors_battery")
    @patch("argus.senses.system.psutil.sensors_temperatures")
    async def test_read(
        self,
        mock_temps,
        mock_battery,
        mock_net,
        mock_disk,
        mock_mem,
        mock_cpu_count,
        mock_cpu_percent,
    ):
        mock_mem.return_value = MagicMock(
            total=16_000_000_000, used=8_000_000_000, percent=50.0
        )
        mock_disk.return_value = MagicMock(
            total=500_000_000_000, used=250_000_000_000
        )
        mock_net.return_value = MagicMock(
            bytes_sent=1_000_000, bytes_recv=2_000_000
        )
        mock_battery.return_value = MagicMock(
            percent=75.0, power_plugged=False, secsleft=7200
        )
        mock_temps.return_value = {
            "k10temp": [MagicMock(current=45.0, label="Tctl")]
        }

        p = SystemPlugin()
        result = await p.read()

        assert result.sensor == "system"
        assert result.error is None
        assert result.text is not None
        assert "CPU: 5.0%" in result.text
        assert "Memory: 50.0%" in result.text
        assert result.data["cpu_count"] == 8
        assert result.data["battery_percent"] == 75.0
        assert result.data["battery_plugged"] is False
        assert "temperatures_c" in result.data

    @patch("argus.senses.system.psutil.cpu_percent", side_effect=Exception("boom"))
    async def test_read_failure(self, mock_cpu):
        p = SystemPlugin()
        result = await p.read()
        assert result.sensor == "system"
        assert result.error == "boom"
