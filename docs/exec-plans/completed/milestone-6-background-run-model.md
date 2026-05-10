# Milestone 6: Background Run Model

Status: completed.

Goal: make QR Watch runnable as a long-lived Windows user-session background
process with safe logging, clean shutdown, and tray controls.

Plan:

- Add runtime config for monitor selection, log directory, screenshot directory,
  and log level.
- Add file logging under the local QR Watch runtime directory.
- Wrap the existing capture/detect/dedup/notify cycle in a background
  controller with start, pause, resume, capture once, and stop behavior.
- Add CLI modes for `--run`, `--tray`, and `--once`.
- Add a pystray-based Windows tray entrypoint with controls for Start, Pause,
  Resume, Capture once, Open logs, Open screenshots, and Exit.
- Document start, stop, and inspection commands.
- Cover controller and CLI behavior with tests.

Validation:

- `conda run -n qrwatch python -m pytest`
- `python tools/validate_harness_structure.py`
