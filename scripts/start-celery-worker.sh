#!/bin/sh
# Wait for readiness marker and call django.setup() before starting celery worker
set -e

MARKER=/app/.web_ready

echo "start-celery-worker: waiting for $MARKER"
while [ ! -f "$MARKER" ]; do
  sleep 1
done
echo "start-celery-worker: found $MARKER, setting up Django and starting worker"

if [ -z "$PYTHONPATH" ]; then
  export PYTHONPATH=/app
fi

python - <<'PY'
import django
django.setup()
print('django.setup() complete in celery worker wrapper')
PY

python - <<'PY'
import django
from importlib import import_module

django.setup()
print('django.setup() complete in celery worker wrapper')

mod = import_module('src.celery_app')
app = getattr(mod, 'app')

app.worker_main(argv=['worker', '--loglevel=info'])
PY
