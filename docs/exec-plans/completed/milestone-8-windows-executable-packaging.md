# Milestone 8: Windows Executable Packaging

Status: completed.

Goal: make QR Watch repeatably buildable as a Windows executable that launches safely in dry-run tray mode and uses editable local configuration.

## Completed Work

- Added `src/qrwatch/packaged.py` as the executable entrypoint.
- Packaged runs default to tray mode when no explicit CLI mode is supplied.
- Packaged runs read `%LOCALAPPDATA%\QRWatch\config.env` by default.
- Missing default packaged config files are created with dry-run mode enabled and no credentials.
- Explicit `--config PATH` and `QRWATCH_CONFIG_FILE` paths remain opt-in and must exist.
- Tray UI includes an Open settings file action for the active config file.
- Added `packaging/qrwatch.spec` and `tools/build_windows_executable.ps1`.
- Added `pyinstaller` to `environment.yml`.
- Documented executable build and validation behavior in `docs/PACKAGING.md`, `docs/ENVIRONMENT.md`, `docs/RUNTIME.md`, and `ARCHITECTURE.md`.

## Validation

- `conda env update -n qrwatch -f environment.yml`
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools\build_windows_executable.ps1`
- `.\dist\QRWatch\QRWatch.exe --help`
- `.\dist\QRWatch\QRWatch.exe --capture-once --monitor 0`
  - Startup and default config creation succeeded.
  - Capture returned the expected BitBlt failure in this non-interactive command context.
- `conda run -n qrwatch python -m pytest`: 50 passed.
- `python tools\validate_harness_structure.py`: passed.
