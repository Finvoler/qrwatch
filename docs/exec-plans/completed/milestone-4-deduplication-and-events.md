# Milestone 4 Deduplication And Events

Status: completed.

## Goal

Convert raw QR detections into notification-ready events while suppressing
repeated payloads inside a configurable window.

## Acceptance Criteria

- Detection results are normalized into structured events. Implemented.
- Repeated QR payloads are suppressed for a configurable window. Implemented.
- Local state uses a small JSON store and does not persist raw QR payloads.
  Implemented.
- Tests cover repeated detections, expiry, and multiple QR codes in one frame.
  Implemented.

## Outcome

- Added QR event shaping in `src/qrwatch/events.py`.
- Added configurable deduplication window and state path settings.
- Implemented JSON-backed deduplication state keyed by SHA-256 payload hash.
- Wired `QRWatchApp.capture_once` through event shaping and deduplication.
- Extended CLI capture output with event, notification-ready, and suppressed
  counts without printing raw QR payloads.

## Validation

- `conda run -n qrwatch python -m pytest -q`: passed, 21 tests.
- `python tools/validate_harness_structure.py`: passed.

## Notes

- The first two pytest attempts using pytest-managed temp directories failed
  because the Windows sandbox denied access to those temp roots. The final
  passing run avoids pytest temp fixtures in the new tests.
