$env:DEV_DB_USER = 'postgres'
$env:DEV_DB_PASSWORD = 'postgres'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_HOST = '127.0.0.1'
$env:DEV_DB_PORT = '5432'
& 'C:\Dev\Gold\gchub_db\.venv\Scripts\python.exe' 'manage.py' 'migrate' '--noinput' '--settings=gchub_db.settings' > 'C:\Dev\Gold\gchub_db\dev\migrate_output.txt' 2>&1
