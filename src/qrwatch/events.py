"""QR detection event shaping."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime

from qrwatch.detectors import QRDetection


@dataclass(frozen=True)
class QREvent:
    """Notification-ready QR event.

    The raw payload stays in memory for future notifiers. Persisted state should
    use ``payload_hash`` instead so QR contents are not written to disk.
    """

    payload: str
    payload_hash: str
    source: str
    detected_at: datetime
    corners: tuple[tuple[float, float], ...] = ()


def shape_detection_events(
    detections: tuple[QRDetection, ...],
    *,
    detected_at: datetime,
) -> tuple[QREvent, ...]:
    """Normalize detector results into notification-ready QR events."""

    return tuple(
        QREvent(
            payload=detection.payload,
            payload_hash=hash_payload(detection.payload),
            source=detection.source,
            detected_at=detected_at,
            corners=detection.corners,
        )
        for detection in detections
    )


def hash_payload(payload: str) -> str:
    """Return a stable hash for deduplication without persisting QR contents."""

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
