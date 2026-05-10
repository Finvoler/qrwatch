param(
    [string]$EnvironmentName = "qrwatch",
    [string]$SpecPath = "packaging\qrwatch.spec"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

conda run -n $EnvironmentName pyinstaller --noconfirm --clean $SpecPath

Write-Host "Built QR Watch executable at dist\QRWatch\QRWatch.exe"
