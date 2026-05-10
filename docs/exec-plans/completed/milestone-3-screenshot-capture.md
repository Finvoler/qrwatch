# Milestone 3 Screenshot Capture

Status: completed.

## Goal

Start milestone 3 by implementing local screenshot capture with `mss` behind
`src/qrwatch/capture.py`.

## Outcome

- Replaced the capture placeholder with an `mss` backed function that returns
  frame metadata and image pixels in memory.
- Added `qrwatch --capture-once --monitor <index>` for a manual smoke path that
  inspects the screen without saving screenshots by default.
- Added `qrwatch --save-capture <path>` as an explicit opt-in inspection path
  when a human wants to view a captured frame.
- Added focused tests that avoid real desktop capture by using a fake backend.

## Validation

- `python tools/validate_harness_structure.py`: passed.
- `conda run -n qrwatch python -m pytest`: passed, 9 tests.
- `conda run -n qrwatch python -m qrwatch --capture-once`: passed with desktop
  access approval, captured monitor 1 at 1920x1080 without saving an image.

## Notes

Running the manual smoke command inside the default sandbox failed because
Windows `BitBlt` desktop access was blocked. The same command passed when run
with explicit desktop access approval.
