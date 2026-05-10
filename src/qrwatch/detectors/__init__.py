"""OpenCV-backed QR detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass(frozen=True)
class QRDetection:
    """Structured QR detection result.

    The payload is intentionally kept in memory for later event shaping; callers
    should avoid logging or printing it by default.
    """

    payload: str
    source: str
    corners: tuple[tuple[float, float], ...] = ()


class DetectorBackendUnavailable(RuntimeError):
    """Raised when the QR detection backend cannot be imported."""


class QRDetectionError(RuntimeError):
    """Raised when QR detection fails for a frame."""


def detect_qr_codes(
    pixels: np.ndarray,
    *,
    source: str = "frame",
    detector_factory: Callable[[], Any] | None = None,
) -> tuple[QRDetection, ...]:
    """Detect and decode QR codes from an in-memory image array."""

    cv2 = _load_cv2()
    image = _normalize_image(pixels)
    detector = detector_factory() if detector_factory is not None else cv2.QRCodeDetector()

    try:
        detections = _detect_multi(detector, image, source=source)
        if detections:
            return detections
        return _detect_single(detector, image, source=source)
    except QRDetectionError:
        raise
    except Exception as exc:  # pragma: no cover - backend-specific failures
        raise QRDetectionError(f"failed to detect QR codes in {source}: {exc}") from exc


def _load_cv2() -> Any:
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise DetectorBackendUnavailable(
            "opencv-python is not installed; install the qrwatch environment"
        ) from exc
    return cv2


def _normalize_image(pixels: np.ndarray) -> np.ndarray:
    array = np.asarray(pixels)
    if array.ndim == 2:
        return np.ascontiguousarray(array)
    if array.ndim != 3 or array.shape[2] < 3:
        raise QRDetectionError("QR detection requires a grayscale, BGR, or BGRA image")
    return np.ascontiguousarray(array[:, :, :3])


def _detect_multi(
    detector: Any,
    image: np.ndarray,
    *,
    source: str,
) -> tuple[QRDetection, ...]:
    found, decoded_info, points, _ = detector.detectAndDecodeMulti(image)
    if not found:
        return ()

    return tuple(
        QRDetection(
            payload=payload,
            source=source,
            corners=_corners_for_index(points, index),
        )
        for index, payload in enumerate(decoded_info)
        if payload
    )


def _detect_single(
    detector: Any,
    image: np.ndarray,
    *,
    source: str,
) -> tuple[QRDetection, ...]:
    payload, points, _ = detector.detectAndDecode(image)
    if not payload:
        return ()
    return (
        QRDetection(
            payload=payload,
            source=source,
            corners=_corners_for_index(points, 0),
        ),
    )


def _corners_for_index(points: Any, index: int) -> tuple[tuple[float, float], ...]:
    if points is None:
        return ()

    array = np.asarray(points, dtype=float)
    if array.size == 0:
        return ()
    if array.ndim == 2:
        selected = array
    elif array.ndim >= 3:
        selected = array[index]
    else:
        return ()

    return tuple((float(x), float(y)) for x, y in selected.reshape(-1, 2))
