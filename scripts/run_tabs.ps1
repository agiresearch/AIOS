# Open the four terminal tabs of the scheduling demo, one window each.
#
# Each tab is an independent agent submitting to its own backend, and its
# priority follows that backend: ollama -> high, gemini -> normal, groq -> low.
# The fourth tab pins a priority explicitly, to show that an explicit choice
# wins over the backend default.
#
# Start the kernel first, in its own window:
#   .\scripts\run_kernel.ps1
#
# Usage:
#   .\scripts\run_tabs.ps1              # open the four tabs
#   .\scripts\run_tabs.ps1 -DryRun      # print the commands instead
#
# The kernel's own window is where the scheduling log appears (QUEUED / RUN /
# DONE / READY), so keep it visible while typing into the tabs.

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$VenvPython = Join-Path $RootDir ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = (Get-Command python).Source
}

# name, model, priority ("" = derived from the model's backend)
$Tabs = @(
    @{ Name = "ollama_tab"; Model = "ollama"; Priority = "" },
    @{ Name = "gemini_tab"; Model = "gemini"; Priority = "" },
    @{ Name = "groq_tab";   Model = "groq";   Priority = "" },
    @{ Name = "urgent_tab"; Model = "gemini"; Priority = "high" }
)

foreach ($Tab in $Tabs) {
    $TabArgs = @(
        "scripts/run_terminal.py",
        "--name", $Tab.Name,
        "--model", $Tab.Model,
        "--mode", "chat"
    )
    if ($Tab.Priority -ne "") {
        $TabArgs += @("--priority", $Tab.Priority)
    }

    if ($DryRun) {
        Write-Host "& `"$Python`" $($TabArgs -join ' ')"
    } else {
        Start-Process -FilePath $Python -ArgumentList $TabArgs -WorkingDirectory $RootDir
    }
}

if (-not $DryRun) {
    Write-Host "Opened $($Tabs.Count) tabs. Type a message in each and watch the kernel window."
}
