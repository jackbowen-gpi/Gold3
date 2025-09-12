#!/bin/sh
# Wait for the web service to create the readiness marker, then exec celery beat.
set -e

# Path marker created by the web service when it is ready
MARKER=/app/.web_ready

# How many seconds to wait for the marker before exiting. If unset or 0,
# wait indefinitely. Can be set from docker-compose or env.
WAIT_TIMEOUT=${WAIT_TIMEOUT:-0}
# Sleep interval between checks (seconds)
WAIT_INTERVAL=${WAIT_INTERVAL:-1}

echo "wait-and-start-celery-beat: waiting for $MARKER (timeout=${WAIT_TIMEOUT:-infinite}s)"
start_ts=$(date +%s)
while [ ! -f "$MARKER" ]; do
  if [ "$WAIT_TIMEOUT" -ne 0 ]; then
    now_ts=$(date +%s)
    elapsed=$((now_ts - start_ts))
    if [ "$elapsed" -ge "$WAIT_TIMEOUT" ]; then
      echo "wait-and-start-celery-beat: timeout waiting for $MARKER after ${elapsed}s" >&2
      exit 1
    fi
  fi
  sleep "$WAIT_INTERVAL"
done
echo "wait-and-start-celery-beat: found $MARKER after $(( $(date +%s) - start_ts ))s, starting celery beat"

# Ensure /app is on PYTHONPATH (compose sets PYTHONPATH, but be defensive).
# Append instead of overwrite so existing paths are preserved.
if [ -z "$PYTHONPATH" ]; then
  export PYTHONPATH=/app
else
  case ":$PYTHONPATH:" in
    *:"/app":*) ;;
    *) export PYTHONPATH="$PYTHONPATH":/app ;;
  esac
fi

# Single in-process Python start: run django.setup(), set the beat scheduler
# on the Celery app at runtime (to avoid Celery importing the scheduler module
# at CLI parse time), then start the beat service in the same process.
# Use exec so the Python process replaces this shell script and receives
# signals (SIGTERM) from the container runtime.
exec python - <<'PY'
import django
from importlib import import_module
import sys

django.setup()
print('django.setup() complete in celery-beat wrapper')

# Import the project's Celery app and configure the beat scheduler to use our
# lazy wrapper; setting app.conf.beat_scheduler before starting prevents the
# CLI from importing the scheduler module early.
mod = import_module('src.celery_app')
app = getattr(mod, 'app')

# Use the lazy wrapper scheduler we added in the repo. We set the configuration
# to the module:Class string which Celery understands, and also set the value
# directly to be defensive.
app.conf.beat_scheduler = 'src.lazy_beat_scheduler:LazyDatabaseScheduler'
try:
  lazy_mod = import_module('src.lazy_beat_scheduler')
  app.conf.beat_scheduler_class = getattr(lazy_mod, 'LazyDatabaseScheduler')
except Exception:
  # If the module isn't importable yet, rely on the string path above.
  pass

# Start beat using the app instance. We omit CLI scheduler flags so Celery
# doesn't attempt to resolve the scheduler from CLI args (which can trigger
# early imports). When calling app.start(), pass the Celery subcommand as the
# first item (for example, 'beat') instead of a tool name like 'celery'.
argv = ['beat', '--loglevel=info']
app.start(argv)
PY
