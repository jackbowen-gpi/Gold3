Local development Postgres

This project includes a small docker-compose setup to run a local Postgres
instance for development. Use the helper scripts in `scripts/` to start the
database and the Django development server.

Start Postgres and the dev server:

```powershell
.\scripts\start_dev_server.ps1
```

The script will:
- start the Postgres service via `docker compose up -d` (image: postgres:15)
- wait for Postgres to become ready
- set environment variables used by `local_settings.py` and start `manage.py runserver` detached

If you prefer to start Postgres manually, run `docker compose up -d` from
the `dev/` folder.
