Developer quickstart for GOLD

This repo contains the GOLD Django application. These notes are intentionally short and practical for local development.

Prerequisites
- Python 3.11+ (3.13 tested), virtualenv
- Node/npm if you plan to work on frontend builds (Vite)

Quickstart (Windows PowerShell)

```powershell
# activate venv
.venv\Scripts\Activate.ps1

# install deps
pip install -r requirements-dev.txt

# run dev server
$env:PYTHONPATH='C:\Dev\Gold\gchub_db'
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --settings=gchub_db.settings
```

Prefer the wrapper script below for consistency (it always activates the repo .venv):

```powershell
# Start devserver using the repo-local venv (recommended)
.\scripts\start-with-venv.ps1
```

Useful scripts
- `scripts/dev-run.ps1` - helper to start the dev server (see scripts/)
- `scripts/setup-dev.ps1` - helper to bootstrap a dev environment

Testing
```powershell
.venv\Scripts\Activate.ps1
$env:PYTHONPATH='C:\Dev\Gold\gchub_db'
.venv\Scripts\python.exe -m pytest -q
```

Notes
- Contributed debugging helpers and URL resolver dumps are in `scripts/` and `resolver_dump_*.txt`.
- Keep the `conftest.py` tweaks for pytest compatibility when running tests from various working directories.
