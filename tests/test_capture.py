from __future__ import annotations

import numpy as np
import pytest

from qrwatch.capture import CaptureError, capture_screen


class FakeBackend:
    monitors = [
        {"left": 0, "top": 0, "width": 4, "height": 2},
        {"left": 0, "top": 0, "width": 3, "height": 2},
    ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def grab(self, monitor):
        width = monitor["width"]
        height = monitor["height"]
        pixels = np.zeros((height, width, 4), dtype=np.uint8)
        pixels[:, :, 0] = 10
        pixels[:, :, 1] = 20
        pixels[:, :, 2] = 30
        pixels[:, :, 3] = 255
        return pixels


def test_capture_screen_returns_bgr_frame_metadata():
    frame = capture_screen(backend_factory=FakeBackend)

    assert frame.width == 3
    assert frame.height == 2
    assert frame.source == "monitor:1"
    assert frame.color_format == "BGR"
    assert frame.captured_at.tzinfo is not None
    assert frame.captured_at.utcoffset() is not None
    assert frame.pixels.shape == (2, 3, 3)
    assert frame.pixels.flags.c_contiguous
    assert frame.pixels[0, 0].tolist() == [10, 20, 30]


def test_capture_screen_can_capture_all_monitors():
    frame = capture_screen(monitor_index=0, backend_factory=FakeBackend)

    assert frame.width == 4
    assert frame.height == 2
    assert frame.source == "monitor:0"


def test_capture_screen_rejects_missing_monitor():
    with pytest.raises(CaptureError, match="monitor 5"):
        capture_screen(monitor_index=5, backend_factory=FakeBackend)
