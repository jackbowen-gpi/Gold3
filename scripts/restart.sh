#!/bin/bash
# Forces apache2 to reload the Django app. Doesn't restart apache2, but the
# next time somebody browses one of the DB pages, the entire thing is
# reloaded and any changes take affect.
#
# NOTE: The first time someone browses to a page, it will be slow while
# everything is re-cached and re-compiled.

# Use project root as working dir
cd "$(dirname "$0")" || true

# If a virtualenv is present, use its python to run migrations so the DB
# is up-to-date on restart. Fallback to system python if not.
VENV_PY=".venv/bin/python"
if [ -x "$VENV_PY" ]; then
  PY="$VENV_PY"
else
  if command -v python >/dev/null 2>&1; then
    PY="python"
  else
    PY=""
  fi
fi

if [ -z "$PY" ]; then
  echo "No python found to run migrations/makemigrations. Skipping DB steps."
else
  echo "Running: $PY manage.py makemigrations --noinput"
  # make migrations for all apps (idempotent)
  "$PY" manage.py makemigrations --noinput || echo "makemigrations failed (continuing)"

  echo "Running: $PY manage.py migrate --noinput"
  "$PY" manage.py migrate --noinput || echo "migrate failed"
fi

# Touch wsgi config to force reload
touch apache/wsgi_conf.py
