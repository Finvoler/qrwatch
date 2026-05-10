# Milestone 2 Package Skeleton And CLI

Status: completed.

Started: 2026-05-09.
Completed: 2026-05-09.

## Goal

Create the first runnable `qrwatch` Python package without real screenshot capture, QR detection, or external notification sends.

## Completed Scope

- Added `src/qrwatch/` with the product layer boundaries documented in `ARCHITECTURE.md`.
- Added a dry-run CLI and module entrypoint.
- Added configuration loading for interval, notifier provider, dry-run mode, credential source labels, and optional dotenv-style config files.
- Added smoke tests for safe defaults, environment overrides, config-file loading, invalid interval handling, and CLI dry-run startup.
- Added `pyproject.toml` project metadata, console script metadata, package discovery, and pytest configuration.

## Validation

- `conda run -n qrwatch python -m pytest`: passed, 5 tests.
- `conda run -n qrwatch python -m qrwatch`: passed, starts in dry-run mode.
- `python tools/validate_harness_structure.py`: passed.
