# Milestone 3 QR Detection

Status: completed.

## Goal

Complete milestone 3 by implementing OpenCV-backed QR detection behind
`src/qrwatch/detectors/` and wiring it into the one-shot screen inspection path.

## Acceptance Criteria

- QR detection accepts in-memory capture frames without writing screenshots by
  default. Implemented.
- Detector results include structured payload and location metadata for later
  deduplication/event shaping. Implemented.
- Static fixture tests cover QR-positive and QR-negative images. Implemented.
- The CLI smoke path can report how many QR codes were detected without printing
  raw QR payloads. Implemented.
- Harness structure validation and the pytest suite pass. Implemented.

## Outcome

- Replaced the detector placeholder with OpenCV `QRCodeDetector`-backed
  detection.
- Added structured detection results with payload, frame source, and corner
  metadata.
- Wired QR detection into `QRWatchApp.capture_once`.
- Extended the CLI capture path to print detection status and count without
  printing raw QR payloads.
- Added static positive and negative PNG fixtures under `tests/fixtures/images/`.

## Validation

- `python tools/validate_harness_structure.py`: passed.
- `conda run -n qrwatch python -m pytest`: passed, 14 tests.
- `conda run -n qrwatch python -m qrwatch --capture-once`: passed with
  desktop access approval, captured monitor 1 at 1920x1080, reported
  `qr_detections=0`, and did not save a screenshot.
