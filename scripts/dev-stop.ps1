<#
Stop helper: kills any running python processes started by the dev-run helper.
Usage:
  .\scripts\dev-stop.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "Stopping dev server processes (python)..."
$procs = Get-Process | Where-Object { $_.ProcessName -match 'python' }
if (-not $procs) {
    Write-Host "No python processes found."
    exit 0
}

$procs | Select-Object Id, ProcessName, StartTime | Format-Table -AutoSize

$confirm = Read-Host "Kill these processes? (y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "Aborting."
    exit 0
}

$procs | ForEach-Object { Stop-Process -Id $_.Id -Force }
Write-Host "Processes killed."
