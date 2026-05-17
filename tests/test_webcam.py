"""Tests for webcam plugin."""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from argus.senses.webcam import WebcamPlugin


class TestWebcamPlugin:
    @patch("argus.senses.webcam.cv2.VideoCapture")
    @patch("argus.senses.webcam._HAS_CV2", True)
    async def test_probe_success(self, mock_cap_class):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap_class.return_value = mock_cap

        p = WebcamPlugin()
        assert await p.probe() is True
        mock_cap.release.assert_called_once()

    @patch("argus.senses.webcam._HAS_CV2", False)
    async def test_probe_no_opencv(self):
        p = WebcamPlugin()
        assert await p.probe() is False

    @patch("argus.senses.webcam.cv2.VideoCapture")
    @patch("argus.senses.webcam.cv2.cvtColor")
    @patch("argus.senses.webcam.Image.fromarray")
    @patch("argus.senses.webcam._HAS_CV2", True)
    async def test_read_success(self, mock_fromarray, mock_cvt, mock_cap_class):
        from PIL import Image as PILImage
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        # Return a fake BGR frame
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, fake_frame)
        mock_cap_class.return_value = mock_cap
        # Return a real small image
        mock_fromarray.return_value = PILImage.new("RGB", (640, 480))

        p = WebcamPlugin()
        result = await p.read()

        assert result.sensor == "webcam"
        assert result.error is None
        assert result.image is not None
        assert len(result.image) > 0
        assert result.data["width"] == 640
        assert result.data["height"] == 480

    @patch("argus.senses.webcam.cv2.VideoCapture")
    @patch("argus.senses.webcam._HAS_CV2", True)
    async def test_read_frame_failure(self, mock_cap_class):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_cap_class.return_value = mock_cap

        p = WebcamPlugin()
        result = await p.read()
        assert result.sensor == "webcam"
        assert result.error is not None

    @patch("argus.senses.webcam.cv2.VideoCapture")
    @patch("argus.senses.webcam._HAS_CV2", True)
    async def test_close(self, mock_cap_class):
        mock_cap = MagicMock()
        mock_cap_class.return_value = mock_cap

        p = WebcamPlugin()
        p._cap = mock_cap
        await p.close()
        mock_cap.release.assert_called_once()
        assert p._cap is None

    def test_mcp_tools(self):
        p = WebcamPlugin()
        tools = p.mcp_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "argus_webcam_capture"
