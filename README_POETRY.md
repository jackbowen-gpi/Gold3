Poetry setup for Gold (gchub_db)

Steps to use Poetry locally (Windows PowerShell):

1. Install Poetry (if not installed):

   iwr -useb https://install.python-poetry.org | python -

2. From the project root (where this README is), create a venv managed by Poetry:

   poetry env use C:\Path\To\Python3.11

3. Import existing dependencies (optional):

   poetry add $(cat requirements.txt)

   If some dependencies fail to build, add them one-by-one and handle platform-specific
   build requirements. Prefer pinning versions compatible with Python 3.13.

4. Install development dependencies and activate the shell:

   poetry install
   poetry shell

5. Run Django inside Poetry environment:

   PYTHONPATH='C:\Dev\Gold' python -m django runserver --settings=gchub_db.settings

Notes:
- This repo uses a non-standard layout (project package `gchub_db` inside the repo root). Keep
  PYTHONPATH pointing to the workspace root when running Django so imports resolve.
- I created a minimal `pyproject.toml` with Django pinned. Expand dependencies after testing.
