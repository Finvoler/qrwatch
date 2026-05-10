# Packaging

QRWatch uses PyInstaller to build a Windows executable.

## Build

From the repository root:

```powershell
.\tools\build_windows_executable.ps1
```

Equivalent direct command:

```powershell
pyinstaller --noconfirm --clean packaging\qrwatch.spec
```

Build output is written to ignored `build/` and `dist/` directories. The expected executable path is `dist\QRWatch\QRWatch.exe`.

## Packaged Behavior

The packaged launcher uses `src/qrwatch/packaged.py` and defaults to tray mode when no explicit mode is supplied.

On first launch it uses `%LOCALAPPDATA%\QRWatch\config.env` as the default config path and creates that file if it does not already exist.

## Validation

After installing the environment, these checks are safe:

```powershell
python -m pytest
.\dist\QRWatch\QRWatch.exe --capture-once
.\dist\QRWatch\QRWatch.exe --tray
```
