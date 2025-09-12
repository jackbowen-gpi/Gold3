#!/bin/sh
set -e

echo "Starting notification daemon..."
exec python /app/tools/notification_daemon.py --host 0.0.0.0 --port 5341
