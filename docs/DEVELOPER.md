# DEVELOPER GUIDE — gchub_db

This document contains the essential steps to get the project running locally, how to run tests, and quick troubleshooting.

Prerequisites
- Windows PowerShell (pwsh.exe) or Windows PowerShell
- Python 3.13 (recommended — matches CI)
- Git

Quick start (one-liner)
1. From repo root:

   ```powershell
   # bootstrap: creates .venv, installs deps, migrate
   .\scripts\setup_dev.ps1
   ```

Manual setup

1. Create and activate virtualenv

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies

   ```powershell
   .\.venv\Scripts\python.exe -m pip install --upgrade pip
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Run migrations

   ```powershell
   $env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'
   .\.venv\Scripts\python.exe manage.py migrate --noinput
   ```

4. Optional: load fixtures (if present)

   ```powershell
   .\.venv\Scripts\python.exe manage.py loaddata dev_seed.json
   ```

Run the dev server

```powershell
$env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Run tests (preferred)

```powershell
.\scripts\run_tests.ps1
# or manually:
$env:DJANGO_SETTINGS_MODULE = 'gchub_db.settings'
.\.venv\Scripts\python.exe manage.py test --pattern='test*.py' --top-level-directory='.' -v2
```

Troubleshooting
- Duplicate model RuntimeError: check for stray `__init__.py` at the repo root or leftover shim files named `gchub_db.py` elsewhere on PYTHONPATH.
- Tests not discovered: use the explicit test flags shown above.
- Address already in use when running server: kill existing `manage.py runserver` processes.

Backups & restore
- Pre-change backups were archived in the parent directory as `gchub_db_backups_YYYYMMDD_HHMMSS.zip`.
- To inspect: `Expand-Archive -Path ..\gchub_db_backups_YYYYMMDD_HHMMSS.zip -DestinationPath ..\gchub_db_restore_tmp`

If you'd like, I can add a variant `setup_dev.ps1 -Force` that optionally deletes the local DB file after confirmation.
