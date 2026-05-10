from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from qrwatch.detectors import QRDetectionError, detect_qr_codes


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "images"


def _read_fixture(name: str) -> np.ndarray:
    image = cv2.imread(str(FIXTURE_DIR / name))
    assert image is not None
    return image


def test_detect_qr_codes_returns_payload_and_corners_from_positive_fixture():
    image = _read_fixture("qr-positive.png")

    detections = detect_qr_codes(image, source="fixture:positive")

    assert len(detections) == 1
    assert detections[0].payload == "qrwatch:test-payload"
    assert detections[0].source == "fixture:positive"
    assert len(detections[0].corners) == 4


def test_detect_qr_codes_returns_empty_tuple_for_negative_fixture():
    image = _read_fixture("qr-negative.png")

    assert detect_qr_codes(image, source="fixture:negative") == ()


def test_detect_qr_codes_rejects_unsupported_image_shape():
    with pytest.raises(QRDetectionError, match="requires"):
        detect_qr_codes(np.zeros((10,), dtype=np.uint8))

