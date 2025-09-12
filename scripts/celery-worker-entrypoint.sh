#!/bin/sh
set -e

MAX_TRIES=${MAX_TRIES:-30}
SLEEP_SECONDS=${SLEEP_SECONDS:-2}

echo "Waiting for web readiness marker..."
i=0
while [ $i -lt $MAX_TRIES ]; do
  if [ -f /app/.web_ready ]; then
    echo "Found web readiness marker. Starting worker."
    break
  fi
  i=$((i+1))
  echo "Waiting for web readiness marker... attempt $i/$MAX_TRIES"
  sleep $SLEEP_SECONDS
done

if [ $i -ge $MAX_TRIES ]; then
  echo "Timed out waiting for web readiness marker; starting worker anyway."
fi

exec celery -A src.celery_app worker --loglevel=info
