Write-Host "Stopping any manage.py runserver processes started from this repo..."
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -match 'manage\.py.*runserver' }
if ($procs) {
    $procs | ForEach-Object { Write-Host "Stopping PID $($_.ProcessId)"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "Stopped $($procs.Count) process(es)."
} else {
    Write-Host 'No runserver processes found.'
}
