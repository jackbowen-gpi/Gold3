param(
    [string]$DbPassword = 'gchub'
)
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Push-Location $repoRoot
$env:USE_PG_DEV = '1'
$env:DEV_DB_HOST = '127.0.0.1'
$env:DEV_DB_PORT = '5433'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_USER = 'gchub'
$env:DEV_DB_PASSWORD = $DbPassword

$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { Write-Error "venv python not found at $python"; Pop-Location; exit 1 }

Write-Host "Running Django shell check for workflow Job count..."
& $python manage.py shell -c "from workflow.models import Job; print('workflow_job count:', Job.objects.count()); print('Latest 5 jobs:'); [print(j.id, getattr(j,'name',None), getattr(j,'workflow_id',None), getattr(j,'is_deleted',None), getattr(j,'status',None)) for j in Job.objects.order_by('-id')[:5]]"

Pop-Location
