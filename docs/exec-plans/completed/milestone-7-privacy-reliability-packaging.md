# Milestone 7: Privacy, Reliability, And Packaging

Status: completed.

## Goal

Harden QR Watch for real personal use by making privacy behavior explicit,
bounding screenshot retention, strengthening failure handling, and documenting
generated packaging/runtime outputs.

## Completed Scope

- Added configurable screenshot retention with count and age limits.
- Kept automatic screenshot saving disabled by default.
- Documented QR payload persistence as hash-only deduplication state.
- Added tests for screenshot retention, privacy config, notification failures,
  degraded background failure handling, and restart deduplication behavior.
- Documented runtime output, generated files, and packaging expectations.

## Validation

- `python tools/validate_harness_structure.py` passed.
- `$env:PYTHONIOENCODING='utf-8'; conda run -n qrwatch python -m pytest`
  passed with 44 tests.

