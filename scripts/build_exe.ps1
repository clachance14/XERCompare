# Build the windowed desktop app using local dependencies.
param([string]$Python = '')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not $Python) {
    $Python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
    if (-not (Test-Path $Python)) { $Python = 'python' }
}
& $Python scripts/build_windows.py
if ($LASTEXITCODE -ne 0) { throw "Windows EXE build failed (exit $LASTEXITCODE)" }
Write-Host 'Double-click dist\XERCompare.exe.'
