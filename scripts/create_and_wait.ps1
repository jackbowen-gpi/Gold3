param(
    [int]$WaitSeconds = 10
)

Write-Host "Running create_periodic_task.py inside web container..."
docker-compose exec web python scripts/create_periodic_task.py

Write-Host "Waiting $WaitSeconds seconds for worker to process task..."
Start-Sleep -Seconds $WaitSeconds

Write-Host "Tailing celery logs (last 200 lines):"
docker-compose logs --tail=200 celery
