# Start the AIOS kernel server (PowerShell equivalent of run_kernel.sh).
#
# Two things are easy to get wrong on Windows, and this script handles both:
#
#   interpreter
#       `python` on PATH is usually *not* the project venv -- a global 3.13
#       install has no litellm and fails with ModuleNotFoundError. The venv in
#       this repository is the one with the dependencies, so it is preferred.
#
#   PYTHONUTF8 / PYTHONIOENCODING / PYTHONPATH
#       runtime/launch.py prints emoji in its start-up messages; on a console
#       whose encoding is cp1252 (the Windows default when output is
#       redirected) those prints raise UnicodeEncodeError and stop the kernel
#       before it binds a port. `aios` is also not an installed package, so the
#       project root has to be importable.
#
# Usage:
#   .\scripts\run_kernel.ps1                          # DEBUG logging (as before)
#   $env:AIOS_LOG_LEVEL = "WARNING"; .\scripts\run_kernel.ps1   # quiet

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RootDir

$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = (Get-Command python).Source
}

$env:PYTHONUNBUFFERED = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONPATH = if ($env:PYTHONPATH) { "$RootDir;$env:PYTHONPATH" } else { $RootDir }
if (-not $env:AIOS_LOG_LEVEL) { $env:AIOS_LOG_LEVEL = "DEBUG" }

Write-Host "AIOS kernel"
Write-Host "  root       : $RootDir"
Write-Host "  interpreter: $Python"
Write-Host "  log level  : $env:AIOS_LOG_LEVEL"
Write-Host "  policy     : from scheduler.policy in config.yaml (default: fifo)"
Write-Host ""
Write-Host "The first start takes one to two minutes while the kernel imports"
Write-Host "its components. Press Ctrl-C to stop."
Write-Host ""

& $Python "runtime/launch.py"
