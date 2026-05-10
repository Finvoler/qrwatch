"""Screenshot capture abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import numpy as np


MSS_MONITOR_ALL = 0
MSS_MONITOR_PRIMARY = 1


@dataclass(frozen=True)
class Frame:
    """Captured frame pixels and metadata.

    Pixels are stored as a contiguous BGR array so OpenCV QR detection can use
    the frame without an extra color conversion.
    """

    width: int
    height: int
    source: str
    pixels: np.ndarray
    captured_at: datetime
    color_format: str = "BGR"


class CaptureBackendUnavailable(RuntimeError):
    """Raised when the screenshot backend cannot be imported."""


class CaptureError(RuntimeError):
    """Raised when the screenshot backend cannot capture a frame."""


def capture_screen(
    *,
    monitor_index: int = MSS_MONITOR_PRIMARY,
    backend_factory: Callable[[], Any] | None = None,
) -> Frame:
    """Capture a monitor into memory without writing a screenshot to disk."""

    if monitor_index < 0:
        raise CaptureError("monitor index must be zero or greater")

    factory = backend_factory or _load_mss_factory()

    try:
        with factory() as backend:
            monitor = _select_monitor(backend.monitors, monitor_index)
            screenshot = backend.grab(monitor)
    except CaptureError:
        raise
    except Exception as exc:  # pragma: no cover - backend-specific failures
        raise CaptureError(f"failed to capture monitor {monitor_index}: {exc}") from exc

    pixels = _screenshot_to_bgr(screenshot)
    height, width = pixels.shape[:2]
    return Frame(
        width=width,
        height=height,
        source=f"monitor:{monitor_index}",
        pixels=pixels,
        captured_at=datetime.now().astimezone(),
    )


def _load_mss_factory() -> Callable[[], Any]:
    try:
        from mss import MSS
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise CaptureBackendUnavailable(
            "mss is not installed; install the qrwatch environment"
        ) from exc
    return MSS


def _select_monitor(monitors: Any, monitor_index: int) -> Any:
    try:
        return monitors[monitor_index]
    except IndexError as exc:
        available = max(len(monitors) - 1, 0)
        raise CaptureError(
            f"monitor {monitor_index} is not available; found {available} monitor(s)"
        ) from exc


def _screenshot_to_bgr(screenshot: Any) -> np.ndarray:
    array = np.asarray(screenshot)
    if array.ndim != 3 or array.shape[2] < 3:
        try:
            array = np.frombuffer(screenshot.bgra, dtype=np.uint8).reshape(
                (screenshot.height, screenshot.width, 4)
            )
        except AttributeError as exc:
            raise CaptureError("screenshot backend returned unsupported image data") from exc

    return np.ascontiguousarray(array[:, :, :3])


def save_frame_png(frame: Frame, output_path: str | Path) -> Path:
    """Save an explicitly requested capture frame as a PNG."""

    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise CaptureBackendUnavailable(
            "opencv-python is not installed; install the qrwatch environment"
        ) from exc

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame.pixels):
        raise CaptureError(f"failed to save capture to {path}")
    return path
