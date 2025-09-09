# Sets Postgres dev env to use the gchub role and runs the tmp_model_counts.py script
$env:USE_PG_DEV = '1'
$env:DEV_DB_NAME = 'gchub_dev'
$env:DEV_DB_HOST = 'localhost'
$env:DEV_DB_PORT = '5432'
$env:DEV_DB_USER = 'gchub'
$env:DEV_DB_PASSWORD = 'gchub'

python .\scripts\tmp_model_counts.py | Tee-Object -FilePath .\model_counts.log
