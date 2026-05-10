from __future__ import annotations

from datetime import datetime, timezone

from qrwatch.detectors import QRDetection
from qrwatch.events import hash_payload, shape_detection_events


def test_shape_detection_events_preserves_payload_in_memory_and_hashes_it():
    detected_at = datetime(2026, 5, 10, 12, tzinfo=timezone.utc)
    detections = (
        QRDetection(
            payload="qrwatch:test-payload",
            source="fixture:positive",
            corners=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)),
        ),
    )

    events = shape_detection_events(detections, detected_at=detected_at)

    assert len(events) == 1
    assert events[0].payload == "qrwatch:test-payload"
    assert events[0].payload_hash == hash_payload("qrwatch:test-payload")
    assert events[0].source == "fixture:positive"
    assert events[0].detected_at == detected_at
    assert len(events[0].corners) == 4
